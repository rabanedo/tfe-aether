#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
publish.py — Publicación de productos GeoTIFF en GeoServer (Nodo 2 Aether).

Recorre los directorios de productos generados por el pipeline de procesamiento
y notifica a GeoServer vía REST API para que registre cada fichero .tif como
un nuevo granulo en el coveragestore ImageMosaic correspondiente.

Solo publica granulos que no estén ya indexados en GeoServer, lo que hace
el script idempotente: puede ejecutarse varias veces sin crear duplicados.

Uso:
    python publish.py -p /dwh/data
    python publish.py -p /dwh/data --products s2ndvi s2rgb --dry-run

Variables de entorno requeridas (definidas en .env o en el entorno del sistema):
    CDSE_GEOSERVER_USER      Usuario de la REST API de GeoServer
    CDSE_GEOSERVER_PASS      Contraseña de la REST API de GeoServer
    CDSE_GEOSERVER_REST_URL  Endpoint REST para harvesting de granulos.
                             Usa *coverage_name* como placeholder (aparece 2 veces).
                             Formato: .../coveragestores/*coverage_name*/external.imagemosaic
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
            if key not in os.environ:
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


def _granules_url(rest_url_template: str, coverage_name: str) -> str:
    """
    Construye la URL del endpoint de granulos a partir de la URL de harvest.

    De:  .../coveragestores/s2ndvi/external.imagemosaic
    A:   .../coveragestores/s2ndvi/coverages/s2ndvi/index/granules.json
    """
    base = rest_url_template.replace("*coverage_name*", coverage_name)
    base = base.replace("/external.imagemosaic", "")
    return f"{base}/coverages/{coverage_name}/index/granules.json"


def _is_already_indexed(
    file_path: Path,
    coverage_name: str,
    rest_url_template: str,
    user: str,
    password: str,
) -> bool:
    """
    Consulta GeoServer si el granulo ya está registrado en el índice del mosaico.

    Usa el campo 'location' de la tabla de granulos en PostgreSQL, que GeoServer
    expone vía REST. Permite que el script sea idempotente: relanzarlo no
    crea entradas duplicadas en el índice.

    Returns:
        True si el granulo ya está indexado. False si no lo está o hay error
        en la consulta (se asume no indexado para intentar publicarlo).
    """
    url = _granules_url(rest_url_template, coverage_name)
    location = file_path.name
    try:
        resp = requests.get(
            url,
            auth=(user, password),
            params={"filter": f"location = '{location}'"},
            timeout=10,
        )
        if resp.status_code == 200:
            features = resp.json().get("features") or []
            return len(features) > 0
        # 404 = coveragestore o coverage no inicializada todavía → no indexado
        if resp.status_code == 404:
            return False
        logger.debug(
            "Comprobación de granulo devolvió HTTP %s para %s",
            resp.status_code, file_path.name,
        )
    except RequestException as exc:
        logger.debug("No se pudo comprobar si %s está indexado: %s", file_path.name, exc)
    # En caso de duda intentamos publicar
    return False


def _publish_file(
    file_path: Path,
    coverage_name: str,
    rest_url_template: str,
    user: str,
    password: str,
    dry_run: bool,
) -> bool:
    """
    Añade file_path como nuevo granulo a un coveragestore ImageMosaic existente.

    Endpoint: POST .../coveragestores/{cs}/external.imagemosaic
    GeoServer 2.28.x acepta la ruta absoluta sin prefijo file:// en el cuerpo
    (text/plain). Responde 202 Accepted si el granulo se registra correctamente.

    Returns:
        True si la publicación fue exitosa (o dry_run), False en caso de error.
    """
    url = rest_url_template.replace("*coverage_name*", coverage_name)
    # absolute() respeta bind mounts y symlinks; resolve() los rompería
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
        help="Ruta al fichero .env (por defecto /opt/aether-publish/.env).",
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

    _load_dotenv(args.env_file)

    user          = _required_env("CDSE_GEOSERVER_USER")
    password      = _required_env("CDSE_GEOSERVER_PASS")
    rest_url      = os.environ.get("CDSE_GEOSERVER_REST_URL", _DEFAULT_REST_URL)
    products_root = Path(args.products_path)

    if not products_root.is_dir():
        logger.error("El directorio de productos no existe: %s", products_root)
        return 1

    total_ok      = 0
    total_fail    = 0
    total_skip    = 0
    total_already = 0

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
            # Idempotencia: no re-publicar granulos ya indexados en GeoServer
            if not args.dry_run and _is_already_indexed(tif, product, rest_url, user, password):
                logger.debug("Ya indexado, omitido: %s", tif.name)
                total_already += 1
                continue

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

    logger.info(
        "Publicación finalizada: ok=%d  ya_indexados=%d  errores=%d  omitidos=%d  dry_run=%s",
        total_ok, total_already, total_fail, total_skip, args.dry_run,
    )

    # Fallo de configuración (sin productos ni directorios) → código 1
    # Fallos individuales de granulos → se loguean pero el servicio no falla
    # para que systemd no marque el timer como fallido por errores transitorios
    if total_ok == 0 and total_already == 0 and total_fail > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())