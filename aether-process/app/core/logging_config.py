from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import settings


def configure_logging() -> None:
    Path(settings.log_dir).mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=[logging.FileHandler(settings.log_path), logging.StreamHandler()],
    )
