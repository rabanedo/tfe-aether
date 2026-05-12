from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from app.services.s2_processor import create_mosaic, is_mosaic_ready
from app.services.catalog_provider import catalog_session
from app.services.feed_service import FeedService

logger = logging.getLogger(__name__)


class MosaicService:
    def run(
        self,
        limit: int | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        processed = 0
        requeried = 0
        failed = 0

        with catalog_session() as catalog:
            timeout = int(catalog.get_system_setting("processing_task_timeout") or 1)
            catalog.cancel_old_mosaic_tasks(timeout)

            tasks = catalog.get_mosaic_tasks_join_workspace(
                status="waiting", limit=limit
            )

            for task in tasks:
                if dry_run:
                    processed += 1
                    continue

                try:
                    if is_mosaic_ready(catalog=catalog, task=task):
                        catalog.update_mosaic_status(task["task_id"], "processing",
                                                     init_time=True)
                        create_mosaic(catalog=catalog, task=task)
                        catalog.update_mosaic_status(task["task_id"], "completed")
                        processed += 1
                    else:
                        first_date = task["first_date"]
                        compare_date = (
                            first_date if isinstance(first_date, dt.date)
                            else dt.datetime.fromisoformat(str(first_date)).date()
                        )
                        days_threshold = int(task.get("days_to_query_mosaic") or 0)
                        if (dt.date.today() - compare_date).days > days_threshold:
                            FeedService().run(
                                workspace_id=task["workspace_id"],
                                date=str(task["sensing_date"]),
                                orbit_id=task["orbit_id"],
                            )
                            requeried += 1

                except Exception:
                    logger.exception("Mosaic task failed task_id=%s",
                                     task.get("task_id"))
                    catalog.rollback()
                    failed += 1

        return {
            "processed": processed,
            "requeried": requeried,
            "failed": failed,
            "dry_run": dry_run,
        }
