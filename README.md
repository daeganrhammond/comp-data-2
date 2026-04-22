# Portfolio Compensation Dashboard

This project turns the compensation source file into an interactive Streamlit web app.

## Core rules

- The source data file stays outside the code logic and is read fresh from disk.
- The app supports `.csv`, `.xlsx`, and `.xlsm` inputs.
- Refresh is tied to the source file signature so replacing the data file updates the app without code changes.
- Backup snapshots of the web app can be created before major visualization changes.

## Default data behavior

The app looks for data in this order:

1. `PORTFOLIO_DATA_PATH` environment variable, if provided.
2. `synthetic_workers.csv` in the project root.
3. The newest supported file in the project root or `data/`.

Supported file types:

- `.csv`
- `.xlsx`
- `.xlsm`

## Run the app

```powershell
python -m streamlit run app.py
```

## Create a backup snapshot

```powershell
python scripts\create_backup.py
```

Backups are stored under `backups\web_app_snapshots`.

## Deploy

This project includes:

- `requirements.txt` for Python dependencies
- `render.yaml` for Render deployment
- `.streamlit/config.toml` for Streamlit behavior/theme
