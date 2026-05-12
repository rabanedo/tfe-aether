from __future__ import annotations

import datetime as dt
import logging
import shlex
import subprocess
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.catalog_provider import catalog_session

logger = logging.getLogger(__name__)


class ProcessService:
    def run(
        self,
        limit: int | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        processed = 0
        mosaics_queued = 0
        failed = 0

        Path(settings.log_dir).mkdir(parents=True, exist_ok=True)
        std_path = Path(settings.log_dir) / "post_download_std.out"
        err_path = Path(settings.log_dir) / "post_download_err.out"

        with catalog_session() as catalog:
            timeout = int(catalog.get_system_setting("processing_task_timeout") or 1)
            catalog.cancel_old_processing_tasks(timeout)

            tasks = catalog.get_process_tasks_join_workspace(
                status="waiting", limit=limit
            )

            for task in tasks:
                if dry_run:
                    processed += 1
                    continue

                try:
                    catalog.update_process_status(task["task_id"], "processing",
                                                  init_time=True)

                    # Usa process_command de la tarea; si no existe, usa el del workspace
                    command = task.get("process_command") or task.get("s2_process_command")
                    params  = task.get("process_params")  or task.get("s2_process_params") or ""

                    cmd = [command, "-f", task["input_file_path"]]
                    cmd.extend(shlex.split(params))
                    if task.get("product_id"):
                        cmd.extend(["--ingest_id", task["product_id"]])

                    with std_path.open("a", encoding="utf-8") as sout, \
                         err_path.open("a", encoding="utf-8") as serr:
                        result = subprocess.run(cmd, stdout=sout, stderr=serr,
                                                check=False)

                    if result.returncode != 0:
                        catalog.update_process_status(task["task_id"], "waiting")
                        failed += 1
                        continue

                    catalog.update_process_status(task["task_id"], "completed",
                                                  finish_time=True)

                    mosaic_def = catalog.get_mosaic_definition(
                        task["workspace_id"], task["orbit_number"]
                    )
                    if mosaic_def:
                        catalog.add_mosaic_task(
                            first_date=dt.date.today(),
                            workspace_id=task["workspace_id"],
                            orbit_id=task["orbit_number"],
                            sensing_date=task["sensing_date"],
                        )
                        mosaics_queued += 1

                    processed += 1

                except Exception:
                    logger.exception("Process task failed task_id=%s",
                                     task.get("task_id"))
                    catalog.rollback()
                    catalog.update_process_status(task["task_id"], "waiting")
                    failed += 1

        return {
            "processed": processed,
            "mosaics_queued": mosaics_queued,
            "failed": failed,
            "dry_run": dry_run,
        }
