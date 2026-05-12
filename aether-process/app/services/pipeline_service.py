from __future__ import annotations

from app.services.cloud_service import CloudCoverageService
from app.services.download_service import DownloadService
from app.services.feed_service import FeedService
from app.services.mosaic_service import MosaicService
from app.services.process_service import ProcessService


class PipelineService:
    def run_all(self, workspace_id=None, date=None, orbit_id=None, limit=None, dry_run=False):
        return {
            "feeds":      FeedService().run(workspace_id=workspace_id, date=date, orbit_id=orbit_id, dry_run=dry_run),
            "cloud":      CloudCoverageService().run(limit=limit, dry_run=dry_run),
            "downloads":  DownloadService().run(limit=limit, dry_run=dry_run),
            "processing": ProcessService().run(limit=limit, dry_run=dry_run),
            "mosaics":    MosaicService().run(limit=limit, dry_run=dry_run),
        }
