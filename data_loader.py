from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.portfolio_comp.config import DATA_DIR, DEFAULT_DATA_PATH, ENV_DATA_PATH, SUPPORTED_EXTENSIONS


NUMERIC_COLUMNS = [
    "salary_range_min",
    "salary_range_mid",
    "salary_range_max",
    "base_pay_compa_ratio",
    "base_pay",
    "bonus_target_pct",
    "bonus_target_amount",
    "total_target_cash",
    "tenure_years",
    "time_in_role_years",
    "performance_rating",
    "rmc_ttc_p50",
    "rmc_ttc_p65",
    "rmc_ttc_p75",
    "rmc_ttc_p75_aged",
    "rmc_base_p50",
    "rmc_base_p65",
    "rmc_base_p75",
    "rmc_base_p90",
]


def discover_data_file() -> Path:
    if ENV_DATA_PATH:
        candidate = Path(ENV_DATA_PATH).expanduser()
        if candidate.exists():
            return candidate

    if DEFAULT_DATA_PATH.exists():
        return DEFAULT_DATA_PATH

    search_roots = [BASE_DIR for BASE_DIR in [DEFAULT_DATA_PATH.parent, DATA_DIR] if BASE_DIR.exists()]
    candidates: list[Path] = []
    for root in search_roots:
        candidates.extend(
            path for path in root.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )

    if not candidates:
        raise FileNotFoundError(
            "No supported data file found. Add a .csv, .xlsx, or .xlsm file to the project root or data folder."
        )

    return max(candidates, key=lambda path: path.stat().st_mtime_ns)


def get_data_signature(data_path: Path) -> dict[str, str | int]:
    stat = data_path.stat()
    modified_at = pd.Timestamp(stat.st_mtime, unit="s").strftime("%Y-%m-%d %H:%M:%S")
    cache_key = f"{stat.st_mtime_ns}-{stat.st_size}-{data_path.name}"
    return {
        "path": str(data_path),
        "modified_at": modified_at,
        "size_bytes": stat.st_size,
        "cache_key": cache_key,
    }


def _read_source_data(data_path: Path) -> pd.DataFrame:
    suffix = data_path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(data_path)
    return pd.read_excel(data_path, engine="openpyxl")


def _coerce_numeric_columns(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    for column in NUMERIC_COLUMNS:
        if column in cleaned.columns:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    return cleaned


def _derive_columns(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    cleaned.columns = [str(column).strip() for column in cleaned.columns]

    if {"base_pay", "salary_range_min", "salary_range_max"}.issubset(cleaned.columns):
        cleaned["pay_range_status"] = "In Range"
        cleaned.loc[cleaned["base_pay"] < cleaned["salary_range_min"], "pay_range_status"] = "Below Range"
        cleaned.loc[cleaned["base_pay"] > cleaned["salary_range_max"], "pay_range_status"] = "Above Range"
    else:
        cleaned["pay_range_status"] = "Unknown"

    if "rmc_match_found" in cleaned.columns:
        cleaned["rmc_match_found"] = cleaned["rmc_match_found"].fillna("Unknown")

    if {"base_pay", "rmc_base_p50"}.issubset(cleaned.columns):
        cleaned["market_gap_to_p50"] = cleaned["base_pay"] - cleaned["rmc_base_p50"]
    else:
        cleaned["market_gap_to_p50"] = pd.NA

    if {"base_pay", "salary_range_mid"}.issubset(cleaned.columns):
        cleaned["salary_mid_gap"] = cleaned["base_pay"] - cleaned["salary_range_mid"]
    else:
        cleaned["salary_mid_gap"] = pd.NA

    date_columns = [
        "hire_date_synthetic",
        "role_start_date_synthetic",
    ]
    for column in date_columns:
        if column in cleaned.columns:
            cleaned[column] = pd.to_datetime(cleaned[column], errors="coerce")

    return cleaned


@st.cache_data(show_spinner=False)
def load_data(data_path: Path, cache_key: str) -> pd.DataFrame:
    del cache_key
    frame = _read_source_data(data_path)
    frame = _coerce_numeric_columns(frame)
    frame = _derive_columns(frame)
    return frame


def build_summary(frame: pd.DataFrame) -> dict[str, float | int]:
    summary = {
        "employee_count": int(len(frame)),
        "avg_base_pay": float(frame["base_pay"].mean()) if "base_pay" in frame.columns else 0.0,
        "median_compa_ratio": float(frame["base_pay_compa_ratio"].median())
        if "base_pay_compa_ratio" in frame.columns
        else 0.0,
        "avg_bonus_target_pct": float(frame["bonus_target_pct"].mean()) if "bonus_target_pct" in frame.columns else 0.0,
        "in_range_count": int((frame["pay_range_status"] == "In Range").sum()),
        "below_range_count": int((frame["pay_range_status"] == "Below Range").sum()),
        "above_range_count": int((frame["pay_range_status"] == "Above Range").sum()),
    }
    if {"base_pay", "rmc_base_p50"}.issubset(frame.columns):
        summary["at_or_above_market_p50"] = int((frame["base_pay"] >= frame["rmc_base_p50"]).sum())
    else:
        summary["at_or_above_market_p50"] = 0
    return summary


def summarize_by_group(frame: pd.DataFrame, group_column: str, sort_column: str = "employee_count") -> pd.DataFrame:
    grouped = (
        frame.groupby(group_column, dropna=False)
        .agg(
            employee_count=("synthetic_employee_id", "count"),
            avg_base_pay=("base_pay", "mean"),
            avg_compa_ratio=("base_pay_compa_ratio", "mean"),
            avg_total_target_cash=("total_target_cash", "mean"),
        )
        .reset_index()
        .sort_values(sort_column, ascending=False)
    )
    return grouped


def top_job_profiles(frame: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
    return (
        frame.groupby("job_profile", dropna=False)
        .agg(
            employee_count=("synthetic_employee_id", "count"),
            avg_base_pay=("base_pay", "mean"),
        )
        .reset_index()
        .sort_values("employee_count", ascending=False)
        .head(top_n)
    )


def compensation_health(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby(["level", "pay_range_status"], dropna=False)
        .agg(employee_count=("synthetic_employee_id", "count"))
        .reset_index()
        .sort_values(["level", "pay_range_status"])
    )
