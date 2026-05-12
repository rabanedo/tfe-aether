from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    workspace_id: Optional[int] = None
    date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    orbit_id: Optional[int] = None
    limit: Optional[int] = Field(default=None, ge=1)
    dry_run: bool = False


class JobResponse(BaseModel):
    ok: bool
    action: str
    requested: dict
    result: dict
