from __future__ import annotations

from contextlib import contextmanager

from app.core.config import settings
from app.repositories.catalog_manager import CatalogManager


@contextmanager
def catalog_session():
    catalog = CatalogManager.from_file(settings.config_file_path)
    try:
        yield catalog
    finally:
        catalog.close()
