from pathlib import Path
import json

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
        valid_templates = ", ".join(AVAILABLE_TEMPLATES)

        raise ValueError(
            f"Invalid HTML report template: {template}. "
            f"Valid templates are: {valid_templates}."
        )

    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )

    html_template = env.get_template(
        AVAILABLE_TEMPLATES[template]
    )

    # Build chart payload (SAFE)
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


def _prepare_chart_data(profile: DatasetProfile) -> dict:
    """Prepare chart data for JavaScript rendering (SAFE VERSION)."""

    columns = []
    null_percents = []
    unique_counts = []

    numeric_distributions = []

    if profile.columns:
        for col in profile.columns:
            columns.append(col.name)
            null_percents.append(round(col.null_percent, 2))
            unique_counts.append(col.unique_count)

            
            if (
                col.numeric_stats
                and col.numeric_stats.histogram
            ):
                hist = col.numeric_stats.histogram

                # safety guards
                if hist.bins and hist.counts:
                    numeric_distributions.append({
                        "name": col.name,
                        "bins": hist.bins,
                        "counts": hist.counts,
                    })

    duplicate_rows = 0
    unique_rows = 0

    if profile.quality and profile.summary:
        duplicate_rows = profile.quality.duplicate_rows
        unique_rows = profile.summary.rows - duplicate_rows

    has_column_charts = len(columns) > 0 and (
        len(null_percents) > 0 or len(unique_counts) > 0
    )

    has_histograms = len(numeric_distributions) > 0

    has_duplicate_chart = profile.quality is not None and profile.summary is not None

    return {
        "columns": columns,
        "nullPercents": null_percents,
        "uniqueCounts": unique_counts,

        "duplicateRows": duplicate_rows,
        "uniqueRows": unique_rows,

        "hasColumnCharts": has_column_charts,
        "hasHistogramCharts": has_histograms,
        "hasDuplicateChart": has_duplicate_chart,

        "numericDistributions": numeric_distributions,
    }