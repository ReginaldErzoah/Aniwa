from enum import Enum
from pathlib import Path

import typer

from aniwa.core.profiler import profile_dataframe
from aniwa.io.readers import read_dataset
from aniwa.reports.console import render_console_report
from aniwa.reports.csv_summary_report import render_csv_summary_report
from aniwa.reports.html_report import render_html_report
from aniwa.reports.json_report import render_json_report
from aniwa.reports.excel_report import render_excel_report
from aniwa.reports.markdown_report import render_markdown_report
from aniwa.models.enums import ReportSection
from aniwa.reports.pdf_report import render_pdf

app = typer.Typer(help="Aniwa — Universal dataset profiling and intelligence.")


class ReportFormat(str, Enum):
    console = "console"
    json = "json"
    html = "html"
    excel = "excel"
    markdown = "markdown"
    csv = "csv"
    pdf = "pdf"

class ProfileMode(str, Enum):
    fast = "fast"
    deep = "deep"

def validate_sections(value: str | None) -> list[str] | None:
    if not value:
        return None

    split_sections = [item.strip() for item in value.split(",")]
    valid_options = [e.value for e in ReportSection]

    for sec in split_sections:
        if sec not in valid_options:
            raise typer.BadParameter(f"Invalid report section: {sec}. Valid options are: {', '.join(valid_options)}.")

    return split_sections

def resolve_sections(include: str | None,exclude: str | None,) -> set[ReportSection]:
    include_sections = validate_sections(include)
    exclude_sections = validate_sections(exclude)

    if include_sections and exclude_sections:
        raise typer.BadParameter("Use either --include or --exclude, not both.")

    all_sections = {section for section in ReportSection}

    if include_sections:
        return {ReportSection(section) for section in include_sections}

    if exclude_sections:
        return all_sections - {ReportSection(section) for section in exclude_sections}

    return all_sections

@app.command()
def profile(
    path: str = typer.Argument(..., help="Path to dataset file."),
    report: ReportFormat = typer.Option(
        ReportFormat.console,
        "--report",
        "-r",
        help="Report format.",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path.",
    ),
    mode: ProfileMode = typer.Option(
        ProfileMode.deep,
        "--mode",
        "-m",
        help="Profiling mode. Use 'fast' for lightweight checks or 'deep' for full profiling.",
    ),
    include: str | None = typer.Option(
        None,
        "--include",
        "-i",
        help="Comma-separated list of report sections to include.",
    ),
    exclude: str | None = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Comma-separated list of report sections to exclude.",
    )
):
    """
    Profile a dataset.
    """
    sections = resolve_sections(include, exclude)

    dataset_path = Path(path)

    if not dataset_path.exists():
        raise typer.BadParameter(f"File does not exist: {path}")

    df = read_dataset(path)
    dataset_profile = profile_dataframe(df, mode=mode.value, sections=sections)

    if report == ReportFormat.console:
        render_console_report(dataset_profile)
        return

    if report == ReportFormat.json:
        json_output = render_json_report(dataset_profile, output)

        if output:
            typer.echo(f"JSON report written to {output}")
        else:
            typer.echo(json_output)

        return

    if report == ReportFormat.html:
        if output is None:
            output = "aniwa_report.html"

        render_html_report(dataset_profile, output)
        typer.echo(f"HTML report written to {output}")
        return

    if report == ReportFormat.excel:
        if output is None:
            output = "aniwa_report.xlsx"
        render_excel_report(dataset_profile, output)
        typer.echo(f"Excel report written to {output}")
        return
    
    if report == ReportFormat.markdown:
        markdown_output = render_markdown_report(dataset_profile, output)

        if output:
            typer.echo(f"Markdown report written to {output}")
        else:
            typer.echo(markdown_output)
    
    if report == ReportFormat.csv:
        if output is None:
            output = "summary.csv"
        render_csv_summary_report(dataset_profile, output)
        typer.echo(f"CSV report written to {output}")
        return
    if report == ReportFormat.pdf:
        if output is None:
            output = "aniwa_report.pdf"

        render_pdf(render_html_report(dataset_profile), output)
        return
