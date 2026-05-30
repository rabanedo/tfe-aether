#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
publish.py — Publicación de productos GeoTIFF en GeoServer (Nodo 2 Aether).

Recorre los directorios de productos generados por el pipeline de procesamiento
y notifica a GeoServer vía REST API para que registre cada fichero .tif como
una nueva cobertura en el coveragestore correspondiente.

Uso:
    python publish.py -p /dwh/data
    python publish.py -p /dwh/data --products s2ndvi s2rgb --dry-run

Variables de entorno requeridas (definidas en .env o en el entorno del sistema):
    CDSE_GEOSERVER_USER      Usuario de la REST API de GeoServer
    CDSE_GEOSERVER_PASS      Contraseña de la REST API de GeoServer
    CDSE_GEOSERVER_REST_URL  URL base del endpoint REST de GeoServer
                             (puede contener el placeholder *coverage_name*)
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import requests
from requests.exceptions import HTTPError, RequestException

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("aether.publish")

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
_DEFAULT_REST_URL = (
    "http://localhost:8080/geoserver/rest/workspaces/aether"
    "/coveragestores/*coverage_name*/external.imagemosaic"
)
_DEFAULT_PRODUCTS = [
    "s2rgb",
    "s2ndvi",
    "s2rgb_mosaic",
    "s2ndvi_mosaic",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_dotenv(env_file: str | None) -> None:
    """Carga variables de entorno desde un fichero .env si existe."""
    path = Path(env_file or "/opt/aether-publish/.env")
    if not path.is_file():
        return
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key not in os.environ:            # el entorno tiene prioridad
                os.environ[key] = value


def _required_env(name: str) -> str:
    """Devuelve el valor de una variable de entorno o aborta con error claro."""
    value = os.environ.get(name)
    if not value:
        logger.error(
            "Variable de entorno '%s' no definida. "
            "Defínela en el fichero .env o en el entorno del sistema.",
            name,
        )
        sys.exit(1)
    return value


def _publish_file(
    file_path: Path,
    coverage_name: str,
    rest_url_template: str,
    user: str,
    password: str,
    dry_run: bool,
) -> bool:
    """
    Notifica a GeoServer que registre file_path como nueva cobertura.

    GeoServer espera una URL tipo 'file:///ruta/al/fichero.tif' en el cuerpo
    de la petición POST, con Content-Type: text/plain.

    Returns:
        True si la publicación fue exitosa (o dry_run), False en caso de error.
    """
    url = rest_url_template.replace("*coverage_name*", coverage_name)
#    body = f"file://{file_path.absolute()}"  # absolute() respeta symlinks; resolve() los rompería
    body = str(file_path.absolute())

    if dry_run:
        logger.info("[DRY-RUN] POST %s  body=%s", url, body)
        return True

    try:
        response = requests.post(
            url,
            auth=(user, password),
            headers={"Content-Type": "text/plain"},
            data=body,
            timeout=30,
        )
        response.raise_for_status()
        logger.info(
            "Publicado OK  coverage=%s  file=%s  status=%s",
            coverage_name, file_path.name, response.status_code,
        )
        return True

    except HTTPError as exc:
        logger.error(
            "Error HTTP %s publicando %s en coverage=%s: %s",
            exc.response.status_code, file_path.name, coverage_name, exc,
        )
    except RequestException as exc:
        logger.error(
            "Error de red publicando %s en coverage=%s: %s",
            file_path.name, coverage_name, exc,
        )
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Publica productos GeoTIFF generados por Aether en GeoServer.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-p", "--products-path",
        required=True,
        metavar="DIR",
        help="Directorio raíz que contiene los subdirectorios de productos.",
    )
    parser.add_argument(
        "--products",
        nargs="+",
        default=_DEFAULT_PRODUCTS,
        metavar="PRODUCT",
        help=(
            "Lista de nombres de producto a publicar. Cada nombre debe "
            "coincidir con un subdirectorio dentro de --products-path y con "
            "el coveragestore de GeoServer."
        ),
    )
    parser.add_argument(
        "--env-file",
        default=None,
        metavar="FILE",
        help="Ruta al fichero .env con las credenciales (por defecto /opt/aether-publish/.env).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra las acciones que se ejecutarían sin enviar ninguna petición.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Activa el nivel DEBUG en el log.",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # -- Cargar .env antes de leer credenciales --------------------------------
    _load_dotenv(args.env_file)

    user         = _required_env("CDSE_GEOSERVER_USER")
    password     = _required_env("CDSE_GEOSERVER_PASS")
    rest_url     = os.environ.get("CDSE_GEOSERVER_REST_URL", _DEFAULT_REST_URL)
    products_root = Path(args.products_path)

    if not products_root.is_dir():
        logger.error("El directorio de productos no existe: %s", products_root)
        return 1

    # -- Iterar productos y ficheros ------------------------------------------
    total_ok    = 0
    total_fail  = 0
    total_skip  = 0

    for product in args.products:
        product_dir = products_root / product

        if not product_dir.is_dir():
            logger.warning("Directorio de producto no encontrado, omitido: %s", product_dir)
            total_skip += 1
            continue

        tif_files = sorted(product_dir.glob("*.tif")) + sorted(product_dir.glob("*.TIF"))

        if not tif_files:
            logger.warning("No se encontraron ficheros .tif en: %s", product_dir)
            total_skip += 1
            continue

        logger.info("── Publicando producto '%s' (%d ficheros) ──", product, len(tif_files))

        for tif in tif_files:
            ok = _publish_file(
                file_path=tif,
                coverage_name=product,
                rest_url_template=rest_url,
                user=user,
                password=password,
                dry_run=args.dry_run,
            )
            if ok:
                total_ok += 1
            else:
                total_fail += 1

    # -- Resumen --------------------------------------------------------------
    logger.info(
        "Publicación finalizada: ok=%d  errores=%d  omitidos=%d  dry_run=%s",
        total_ok, total_fail, total_skip, args.dry_run,
    )

    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
