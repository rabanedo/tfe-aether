from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    app_name: str = os.getenv("CDSE_APP_NAME", "Aether API")
    app_env: str = os.getenv("CDSE_APP_ENV", "production")
    base_dir: str = os.getenv("CDSE_BASE_DIR", "/opt/cdse-api")
    log_dir: str = os.getenv("CDSE_LOG_DIR", "/var/log/cdse")
    log_file: str = os.getenv("CDSE_LOG_FILE", "cdse_api.log")
    config_file_path: str = os.getenv("CDSE_CONFIG_FILE", "/opt/cdse-api/config.txt")
    host: str = os.getenv("CDSE_HOST", "0.0.0.0")
    port: int = int(os.getenv("CDSE_PORT", "8080"))

    @property
    def log_path(self) -> str:
        return str(Path(self.log_dir) / self.log_file)


settings = AppSettings()
