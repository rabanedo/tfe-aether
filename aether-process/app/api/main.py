from __future__ import annotations

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.models.schemas import JobResponse, RunRequest
from app.services.cloud_service import CloudCoverageService
from app.services.download_service import DownloadService
from app.services.feed_service import FeedService
from app.services.mosaic_service import MosaicService
from app.services.pipeline_service import PipelineService
from app.services.process_service import ProcessService

configure_logging()
app = FastAPI(title=settings.app_name, version="1.0.0")


@app.get("/api/v1/health")
def health():
    return {"ok": True, "service": settings.app_name}


@app.post("/api/v1/feeds/run", response_model=JobResponse)
def run_feeds(payload: RunRequest):
    result = FeedService().run(payload.workspace_id, payload.date, payload.orbit_id, payload.dry_run)
    return JobResponse(ok=True, action="feeds.run", requested=payload.model_dump(), result=result)


@app.post("/api/v1/cloud/run", response_model=JobResponse)
def run_cloud(payload: RunRequest):
    result = CloudCoverageService().run(limit=payload.limit, dry_run=payload.dry_run)
    return JobResponse(ok=True, action="cloud.run", requested=payload.model_dump(), result=result)


@app.post("/api/v1/downloads/run", response_model=JobResponse)
def run_downloads(payload: RunRequest):
    result = DownloadService().run(payload.limit, payload.dry_run)
    return JobResponse(ok=True, action="downloads.run", requested=payload.model_dump(), result=result)


@app.post("/api/v1/processing/run", response_model=JobResponse)
def run_processing(payload: RunRequest):
    result = ProcessService().run(payload.limit, payload.dry_run)
    return JobResponse(ok=True, action="processing.run", requested=payload.model_dump(), result=result)


@app.post("/api/v1/mosaics/run", response_model=JobResponse)
def run_mosaics(payload: RunRequest):
    result = MosaicService().run(payload.limit, payload.dry_run)
    return JobResponse(ok=True, action="mosaics.run", requested=payload.model_dump(), result=result)


@app.post("/api/v1/pipeline/run", response_model=JobResponse)
def run_pipeline(payload: RunRequest):
    result = PipelineService().run_all(
        payload.workspace_id, payload.date, payload.orbit_id, payload.limit, payload.dry_run
    )
    return JobResponse(ok=True, action="pipeline.run", requested=payload.model_dump(), result=result)
