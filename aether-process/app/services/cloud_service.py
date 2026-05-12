from __future__ import annotations

"""
cloud_service.py — Worker que rellena cloud_coverage en las tareas de descarga.

Flujo:
  1. Lee todas las download_tasks con cloud_coverage IS NULL y status='waiting'.
  2. Por cada una consulta la API OData de CDSE con $expand=Attributes.
  3. Guarda el valor de cloudCover en la BD.

Se ejecuta como paso independiente (antes o en paralelo al DownloadService).
"""

import logging
import time
from typing import Any

import requests

from app.services.catalog_provider import catalog_session

logger = logging.getLogger(__name__)

# URL base del catálogo CDSE
_ODATA_BASE = (
    "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
)


def _fetch_cloud_cover(product_uuid: str, timeout: int = 10) -> float | None:
    """
    Consulta CDSE OData para obtener el cloudCover real de un producto.
    Devuelve el valor float o None si no está disponible / hay error.
    """
    url = f"{_ODATA_BASE}({product_uuid})?$expand=Attributes"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        for attr in data.get("Attributes") or []:
            if attr.get("Name") == "cloudCover":
                return float(attr["Value"])
    except requests.exceptions.Timeout:
        logger.warning("Timeout fetching cloud cover for uuid=%s", product_uuid)
    except requests.exceptions.HTTPError as exc:
        logger.warning("HTTP %s fetching cloud cover for uuid=%s",
                       exc.response.status_code, product_uuid)
    except Exception:
        logger.exception("Unexpected error fetching cloud cover uuid=%s", product_uuid)
    return None


class CloudCoverageService:
    def run(
        self,
        limit: int | None = None,
        delay: float = 0.2,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Rellena cloud_coverage para las tareas que aún lo tienen a NULL.

        Args:
            limit:   Máximo de tareas a procesar por ejecución (None = todas).
            delay:   Segundos de espera entre llamadas a CDSE para no saturar la API.
            dry_run: Si True, sólo cuenta cuántas tareas necesitan relleno.
        """
        updated = 0
        skipped = 0
        failed  = 0

        with catalog_session() as catalog:
            tasks = catalog.get_download_tasks_without_cloud(limit=limit)

            for task in tasks:
                uuid = task["uuid"]

                if dry_run:
                    skipped += 1
                    logger.info("dry_run: would fetch cloud for uuid=%s product=%s",
                                uuid, task.get("product_id"))
                    continue

                cloud = _fetch_cloud_cover(uuid)

                if cloud is None:
                    failed += 1
                    logger.warning("Could not get cloud cover for uuid=%s", uuid)
                else:
                    catalog.update_download_cloud_coverage(uuid, cloud)
                    updated += 1
                    logger.debug("Cloud cover updated uuid=%s cloud=%.1f%%", uuid, cloud)

                # Pausa cortés entre llamadas a la API de CDSE
                if delay > 0:
                    time.sleep(delay)

        logger.info(
            "CloudCoverageService.run updated=%s skipped=%s failed=%s",
            updated, skipped, failed,
        )
        return {
            "updated": updated,
            "skipped": skipped,
            "failed":  failed,
            "dry_run": dry_run,
        }
