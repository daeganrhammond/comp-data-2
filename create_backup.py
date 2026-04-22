from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.portfolio_comp.config import BACKUP_ROOT


SNAPSHOT_ITEMS = [
    "app.py",
    "requirements.txt",
    "README.md",
    "render.yaml",
    "src",
    ".streamlit",
    "scripts",
]


def main() -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_dir = BACKUP_ROOT / f"working_snapshot_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)

    for item in SNAPSHOT_ITEMS:
        source = BASE_DIR / item
        if not source.exists():
            continue

        destination = backup_dir / source.name
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)

    print(f"Backup created: {backup_dir}")


if __name__ == "__main__":
    main()
