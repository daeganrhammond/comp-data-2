from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
APP_TITLE = "Portfolio Compensation Dashboard"
DEFAULT_REFRESH_SECONDS = 60
BACKUP_ROOT = BASE_DIR / "backups" / "web_app_snapshots"
DATA_DIR = BASE_DIR / "data"
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xlsm"}
DEFAULT_DATA_PATH = BASE_DIR / "synthetic_workers.csv"
ENV_DATA_PATH = os.getenv("PORTFOLIO_DATA_PATH")
