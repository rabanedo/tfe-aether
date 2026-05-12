from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from cdsetool.credentials import Credentials
from cdsetool.download import download_feature

from app.services.catalog_provider import catalog_session

logger = logging.getLogger(__name__)


class DownloadService:
    def run(
        self,
        limit: int | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        processed = 0
        queued_for_processing = 0
        skipped_cloud = 0
        failed = 0

        with catalog_session() as catalog:
            timeout = int(catalog.get_system_setting("download_task_timeout") or 1)
            catalog.cancel_old_download_tasks(timeout)

            tasks = catalog.get_download_tasks_join_workspace(
                status="waiting", limit=limit, only_active=True
            )

            for task in tasks:
                # ── Filtro de cobertura nubosa ────────────────────────────
                # Si cloud_coverage es NULL dejamos pasar (CloudCoverageService aún
                # no ha rellenado el dato). Si supera el umbral del workspace,
                # dejamos la tarea en 'waiting' y la saltamos en esta ejecución.
                cloud = task.get("cloud_coverage")
                max_cloud = task.get("s2_max_cloud_cover")

                if cloud is not None and max_cloud is not None:
                    if float(cloud) > float(max_cloud):
                        logger.info(
                            "Skipping download uuid=%s cloud=%.1f%% > max=%.1f%%",
                            task["uuid"], float(cloud), float(max_cloud),
                        )
                        skipped_cloud += 1
                        continue  # no se toca el estado en BD

                if dry_run:
                    processed += 1
                    continue

                try:
                    catalog.update_download_status(task["uuid"], "downloading",
                                                   init_time=True)

                    # Feature dict compatible con cdsetool en formato OData (>= 0.6)
                    # y GeoJSON legacy (< 0.6). La nueva API lee "Name" en lugar de
                    # properties.title para construir el nombre del fichero descargado.
                    product_name = task["product_id"] + ".SAFE"
                    feature = {
                        # OData (cdsetool >= 0.6)
                        "Id":   task["uuid"],
                        "Name": product_name,
                        # GeoJSON legacy (cdsetool < 0.6)
                        "id": task["uuid"],
                        "properties": {
                            "title": product_name,
                            "services": {
                                "download": {
                                    "url": task["s2_download_url"] + task["uuid"]
                                }
                            },
                        },
                    }
                    credentials = Credentials(task["s2_user"], task["s2_pass"])
                    download_feature(feature, task["s2_download_path"],
                                     {"credentials": credentials})

                    output_file = (
                        f"{task['s2_download_path']}/{task['product_id']}.SAFE.zip"
                    )
                    catalog.update_download_status(
                        task["uuid"], "completed", init_time=False, path=output_file
                    )

                    if not catalog.exist_product(task["product_id"]):
                        sensing_date = task["sensing_date"]
                        if hasattr(sensing_date, "date"):
                            sensing_date = sensing_date.date().isoformat()
                        else:
                            sensing_date = str(sensing_date)

                        catalog.ingest_original_product(
                            url=output_file,
                            ingestion_date=dt.datetime.now().date(),
                            sensing_date=sensing_date,
                            sensor=task["sensor"],
                            tile_data_geometry=task["wkt_geom"],
                            cloud_coverage=task["cloud_coverage"],
                            orbit_number=task["orbit_number"],
                            tile_id=task["tile_id"],
                            product_id=task["product_id"],
                            workspace_id=task["workspace_id"],
                        )

                    if task.get("s2_process_command"):
                        sensing_date = task["sensing_date"]
                        if hasattr(sensing_date, "date"):
                            sensing_date = sensing_date.date().isoformat()
                        else:
                            sensing_date = str(sensing_date)

                        catalog.add_processing_task(
                            input_file_path=output_file,
                            process_command=task["s2_process_command"],
                            process_params=task.get("s2_process_params") or "",
                            workspace_id=task["workspace_id"],
                            uuid=task["uuid"],
                            product_id=task["product_id"],
                            orbit_number=task["orbit_number"],
                            sensing_date=sensing_date,
                        )
                        queued_for_processing += 1

                    processed += 1

                except Exception:
                    logger.exception("Download task failed uuid=%s", task.get("uuid"))
                    catalog.rollback()
                    catalog.update_download_status(task["uuid"], "waiting")
                    failed += 1

        return {
            "processed": processed,
            "queued_for_processing": queued_for_processing,
            "skipped_cloud": skipped_cloud,
            "failed": failed,
            "dry_run": dry_run,
        }
