from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import streamlit as st

from config import APP_TITLE, DEFAULT_REFRESH_SECONDS
from data_loader import (
    build_summary,
    compensation_health,
    discover_data_file,
    get_data_signature,
    load_data,
    summarize_by_group,
    top_job_profiles,
)


THEME = {
    "font": "Georgia, Cambria, serif",
    "bg": "#f5f1e8",
    "surface": "#fffdf8",
    "surface_alt": "#ece5d8",
    "text": "#1f2933",
    "muted": "#6b7280",
    "border": "#d5cabb",
    "accent": "#0f766e",
    "accent_2": "#c26d32",
    "accent_3": "#87a58f",
    "good": "#3f7d58",
    "warn": "#c9852b",
    "bad": "#bd5b4c",
}

IS_RENDER = bool(os.getenv("RENDER")) or bool(os.getenv("RENDER_SERVICE_ID"))

st.set_page_config(page_title=APP_TITLE, page_icon=":bar_chart:", layout="wide")


def format_currency(value: float) -> str:
    return f"${value:,.0f}"


def format_percent(value: float) -> str:
    return f"{value:.1%}"


def apply_theme() -> None:
    theme = THEME
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                radial-gradient(circle at top right, {theme["surface_alt"]} 0%, transparent 28%),
                linear-gradient(180deg, {theme["bg"]} 0%, {theme["bg"]} 100%);
            color: {theme["text"]};
            font-family: {theme["font"]};
        }}
        .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}
        div[data-testid="stMetric"] {{
            background: {theme["surface"]};
            border: 1px solid {theme["border"]};
            border-radius: 18px;
            padding: 0.45rem 0.6rem;
            box-shadow: 0 12px 28px rgba(16, 32, 51, 0.06);
            text-align: center;
        }}
        .pc-hero {{
            background: linear-gradient(135deg, {theme["surface"]} 0%, {theme["surface_alt"]} 100%);
            border: 1px solid {theme["border"]};
            border-radius: 24px;
            padding: 1.4rem 1.5rem;
            margin-bottom: 1rem;
        }}
        .pc-kicker {{
            color: {theme["accent"]};
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }}
        .pc-title {{
            color: {theme["text"]};
            font-size: 2.1rem;
            line-height: 1.1;
            font-weight: 700;
            margin-bottom: 0.4rem;
        }}
        .pc-subtitle {{
            color: {theme["muted"]};
            font-size: 1rem;
            max-width: 62rem;
        }}
        .pc-section-title {{
            color: {theme["text"]};
            font-size: 1.45rem;
            font-weight: 700;
            margin: 1.4rem 0 0.35rem 0;
        }}
        .pc-section-copy {{
            color: {theme["muted"]};
            font-size: 0.98rem;
            margin-bottom: 1rem;
        }}
        .pc-card {{
            background: {theme["surface"]};
            border: 1px solid {theme["border"]};
            border-radius: 22px;
            padding: 1.1rem 1.15rem 0.6rem 1.15rem;
            box-shadow: 0 14px 30px rgba(16, 32, 51, 0.06);
            margin-bottom: 1rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def build_filters(frame: pd.DataFrame) -> pd.DataFrame:
    filtered = frame.copy()
    st.sidebar.header("Filters")

    countries = sorted(value for value in filtered["country"].dropna().unique()) if "country" in filtered.columns else []
    selected_countries = st.sidebar.multiselect("Country", countries, default=countries)
    if selected_countries:
        filtered = filtered[filtered["country"].isin(selected_countries)]

    levels = sorted(value for value in filtered["level"].dropna().unique()) if "level" in filtered.columns else []
    selected_levels = st.sidebar.multiselect("Level", levels, default=levels)
    if selected_levels:
        filtered = filtered[filtered["level"].isin(selected_levels)]

    performance_labels = (
        sorted(value for value in filtered["performance_label"].dropna().unique())
        if "performance_label" in filtered.columns
        else []
    )
    selected_performance = st.sidebar.multiselect(
        "Performance Label",
        performance_labels,
        default=performance_labels,
    )
    if selected_performance:
        filtered = filtered[filtered["performance_label"].isin(selected_performance)]

    range_statuses = (
        sorted(value for value in filtered["pay_range_status"].dropna().unique())
        if "pay_range_status" in filtered.columns
        else []
    )
    selected_statuses = st.sidebar.multiselect("Pay Range Status", range_statuses, default=range_statuses)
    if selected_statuses:
        filtered = filtered[filtered["pay_range_status"].isin(selected_statuses)]

    return filtered


def main() -> None:
    apply_theme()

    data_path = discover_data_file()
    signature = get_data_signature(data_path)
    frame = load_data(data_path, signature["cache_key"])
    filtered = build_filters(frame)

    summary = build_summary(filtered)

    st.markdown(
        f"""
        <section class="pc-hero">
            <div class="pc-kicker">Portfolio Compensation</div>
            <div class="pc-title">{APP_TITLE}</div>
            <div class="pc-subtitle">
                Interactive workforce, pay, and market-alignment dashboard. The app reads directly from the current source
                file and refreshes cleanly when a newer dataset replaces it.
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    left_meta, right_meta = st.columns([3, 2])
    with left_meta:
        st.caption(f"Source file: `{data_path.name}`")
        st.caption(f"Last modified: `{signature['modified_at']}`")
    with right_meta:
        refresh_seconds = st.number_input(
            "Refresh interval (seconds)",
            min_value=15,
            max_value=600,
            value=DEFAULT_REFRESH_SECONDS,
            step=15,
        )
        if st.button("Refresh data now", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        if not IS_RENDER:
            st.caption("Tip: replace the source file and click refresh to load the newest data.")

    metric_cols = st.columns(5)
    metric_cols[0].metric("Employees", f"{summary['employee_count']:,}")
    metric_cols[1].metric("Avg Base Pay", format_currency(summary["avg_base_pay"]))
    metric_cols[2].metric("Median Compa Ratio", format_percent(summary["median_compa_ratio"]))
    metric_cols[3].metric("In Range", f"{summary['in_range_count']:,}")
    metric_cols[4].metric("At/Above Market P50", f"{summary['at_or_above_market_p50']:,}")

    st.markdown('<div class="pc-section-title">Workforce and Pay Structure</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="pc-section-copy">Use the filters to focus the dataset, then explore how pay changes across levels, markets, and job groups.</div>',
        unsafe_allow_html=True,
    )

    level_summary = summarize_by_group(filtered, "level")
    country_summary = summarize_by_group(filtered, "country")
    job_profile_summary = top_job_profiles(filtered)
    range_health = compensation_health(filtered)

    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.markdown('<div class="pc-card">', unsafe_allow_html=True)
        fig = px.bar(
            level_summary,
            x="level",
            y="employee_count",
            color="avg_compa_ratio",
            color_continuous_scale=["#dce9e4", "#0f766e"],
            labels={"employee_count": "Employees", "level": "Level", "avg_compa_ratio": "Avg Compa Ratio"},
            title="Headcount by Level",
        )
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with chart_right:
        st.markdown('<div class="pc-card">', unsafe_allow_html=True)
        fig = px.bar(
            country_summary.head(10),
            x="employee_count",
            y="country",
            orientation="h",
            color="avg_base_pay",
            color_continuous_scale=["#f0d8c8", "#c26d32"],
            labels={"employee_count": "Employees", "country": "Country", "avg_base_pay": "Avg Base Pay"},
            title="Top Countries by Headcount",
        )
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    scatter_left, scatter_right = st.columns(2)
    with scatter_left:
        st.markdown('<div class="pc-card">', unsafe_allow_html=True)
        scatter_frame = filtered.dropna(subset=["base_pay", "base_pay_compa_ratio", "level"])
        fig = px.scatter(
            scatter_frame,
            x="base_pay_compa_ratio",
            y="base_pay",
            color="level",
            hover_data=["employee_name", "job_profile", "country"],
            labels={"base_pay_compa_ratio": "Compa Ratio", "base_pay": "Base Pay"},
            title="Pay vs. Compa Ratio",
        )
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with scatter_right:
        st.markdown('<div class="pc-card">', unsafe_allow_html=True)
        fig = px.histogram(
            filtered,
            x="base_pay_compa_ratio",
            nbins=25,
            color="pay_range_status",
            barmode="overlay",
            color_discrete_map={
                "In Range": THEME["good"],
                "Below Range": THEME["warn"],
                "Above Range": THEME["bad"],
                "Unknown": THEME["muted"],
            },
            labels={"base_pay_compa_ratio": "Compa Ratio"},
            title="Compa Ratio Distribution",
        )
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    lower_left, lower_right = st.columns(2)
    with lower_left:
        st.markdown('<div class="pc-card">', unsafe_allow_html=True)
        fig = px.bar(
            range_health,
            x="level",
            y="employee_count",
            color="pay_range_status",
            barmode="stack",
            color_discrete_map={
                "In Range": THEME["good"],
                "Below Range": THEME["warn"],
                "Above Range": THEME["bad"],
                "Unknown": THEME["muted"],
            },
            labels={"employee_count": "Employees", "level": "Level", "pay_range_status": "Range Status"},
            title="Range Health by Level",
        )
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with lower_right:
        st.markdown('<div class="pc-card">', unsafe_allow_html=True)
        fig = px.bar(
            job_profile_summary,
            x="employee_count",
            y="job_profile",
            orientation="h",
            color="avg_base_pay",
            color_continuous_scale=["#dde6f3", "#476c9b"],
            labels={"employee_count": "Employees", "job_profile": "Job Profile", "avg_base_pay": "Avg Base Pay"},
            title="Top Job Profiles",
        )
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="pc-section-title">Employee Detail</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="pc-section-copy">This table stays tied to the active filters, so it can be used as a drill-down view during dashboard review.</div>',
        unsafe_allow_html=True,
    )

    preferred_columns = [
        "synthetic_employee_id",
        "employee_name",
        "country",
        "state_of_residence",
        "zone",
        "job_profile",
        "level",
        "base_pay",
        "salary_range_mid",
        "base_pay_compa_ratio",
        "rmc_base_p50",
        "market_gap_to_p50",
        "performance_label",
        "pay_range_status",
    ]
    visible_columns = [column for column in preferred_columns if column in filtered.columns]
    st.dataframe(filtered[visible_columns], use_container_width=True, hide_index=True)

    st.caption(
        f"Refresh guidance: replace the source file, then reload the page or use the refresh button. Suggested check cadence: every {refresh_seconds} seconds while reviewing updates."
    )


if __name__ == "__main__":
    main()
