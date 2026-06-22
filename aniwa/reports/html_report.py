from pathlib import Path
import json
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from aniwa.models.profile import DatasetProfile


AVAILABLE_TEMPLATES = {
    "default": "default.html",
    "clean": "clean.html",
    "compact": "compact.html",
    "enterprise": "enterprise.html",
    "dark": "dark.html",
}


def render_html_report(
    profile: DatasetProfile,
    output: str | None = None,
    template: str = "default",
) -> str:
    template_dir = Path(__file__).parent / "templates"

    if template not in AVAILABLE_TEMPLATES:
        valid_templates = ", ".join(AVAILABLE_TEMPLATES.keys())
        raise ValueError(
            f"Invalid HTML report template: {template}. "
            f"Valid templates are: {valid_templates}."
        )

    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )

    html_template = env.get_template(AVAILABLE_TEMPLATES[template])

    # Build chart payload
    chart_data = _prepare_chart_data(profile)

    chart_data_json = json.dumps(chart_data, ensure_ascii=False)

    html = html_template.render(
        profile=profile,
        chart_data_json=chart_data_json,
    )

    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_text(html, encoding="utf-8")

    return html


def _prepare_chart_data(profile: DatasetProfile) -> dict[str, Any]:
    """
    Prepare all chart-ready data for enterprise HTML reports.
    Includes:
    - column metrics
    - histogram distributions
    - duplicate summary
    """

    columns: list[str] = []
    null_percents: list[float] = []
    unique_counts: list[int] = []

    histograms: list[dict[str, Any]] = []

    # ----------------------------
    # COLUMN DATA
    # ----------------------------
    if profile.columns:
        for col in profile.columns:
            columns.append(col.name)
            null_percents.append(round(col.null_percent or 0.0, 2))
            unique_counts.append(col.unique_count or 0)

            # ----------------------------
            # HISTOGRAM EXTRACTION (FIXED)
            # ----------------------------
            if (
                col.numeric_stats
                and col.numeric_stats.histogram
                and col.numeric_stats.histogram.bins
                and col.numeric_stats.histogram.counts
            ):
                hist = col.numeric_stats.histogram

                histograms.append({
                    "name": col.name,
                    "bins": hist.bins,
                    "counts": hist.counts,
                })

    # ----------------------------
    # DUPLICATE METRICS
    # ----------------------------
    duplicate_rows = 0
    unique_rows = 0

    if profile.quality and profile.summary:
        duplicate_rows = profile.quality.duplicate_rows or 0
        unique_rows = max(profile.summary.rows - duplicate_rows, 0)

    # ----------------------------
    # CHART FLAGS
    # ----------------------------
    has_column_charts = bool(columns)
    has_histogram_charts = len(histograms) > 0
    has_duplicate_chart = (
        profile.quality is not None
        and profile.summary is not None
    )

    return {
        # column charts
        "columns": columns,
        "nullPercents": null_percents,
        "uniqueCounts": unique_counts,

        # histogram charts (NEW CORE FEATURE)
        "histograms": histograms,
        "hasHistogramCharts": has_histogram_charts,

        # duplicates
        "duplicateRows": duplicate_rows,
        "uniqueRows": unique_rows,
        "hasDuplicateChart": has_duplicate_chart,

        # global chart flag
        "hasColumnCharts": has_column_charts,
    }