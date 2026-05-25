import platform
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import polars as pl
import typer

from aniwa import __version__
from aniwa.config import get_flattened_config
from aniwa.core.profiler import profile_dataframe
from aniwa.io.readers import read_dataset
from aniwa.models.enums import ReportSection
from aniwa.models.profile import ProfileMetadata
from aniwa.reports.console import render_console_report
from aniwa.reports.excel_report import render_excel_report
from aniwa.reports.html_report import render_html_report
from aniwa.reports.json_report import render_json_report
from aniwa.reports.markdown_report import render_markdown_report
from aniwa.reports.pdf_report import render_pdf_report
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn


app = typer.Typer(help="Aniwa - Universal dataset profiling and intelligence.")


CONFIG_FILE_NAMES = (
    "aniwa.yaml",
    "aniwa.yml",
    "aniwa.toml",
    "aniwa.json",
)


class ReportFormat(str, Enum):
    console = "console"
    json = "json"
    html = "html"
    excel = "excel"
    markdown = "markdown"
    pdf = "pdf"


class ProfileMode(str, Enum):
    fast = "fast"
    deep = "deep"


def validate_sections(value: str | None) -> list[str] | None:
    if not value:
        return None

    split_sections = [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]

    if not split_sections:
        return None

    valid_options = [section.value for section in ReportSection]

    for section in split_sections:
        if section not in valid_options:
            raise typer.BadParameter(
                f"Invalid report section: {section}. "
                f"Valid options are: {', '.join(valid_options)}."
            )

    return split_sections


def resolve_sections(
    include: str | None,
    exclude: str | None,
) -> set[ReportSection]:
    include_sections = validate_sections(include)
    exclude_sections = validate_sections(exclude)

    if include_sections and exclude_sections:
        raise typer.BadParameter("Use either --include or --exclude, not both.")

    all_sections = set(ReportSection)

    if include_sections:
        return {ReportSection(section) for section in include_sections}

    if exclude_sections:
        return all_sections - {ReportSection(section) for section in exclude_sections}

    return all_sections


def discover_config_file() -> str | None:
    for filename in CONFIG_FILE_NAMES:
        path = Path.cwd() / filename

        if path.exists():
            return str(path)

    return None


def load_active_config(config_file: str | None) -> dict[str, Any]:
    if config_file:
        path = Path(config_file)

        if not path.exists():
            raise typer.BadParameter(f"Configuration file not found: {config_file}")

        try:
            return get_flattened_config(str(path))
        except ValueError as exc:
            raise typer.BadParameter(f"Configuration error: {exc}") from exc

    discovered_config = discover_config_file()

    if discovered_config is None:
        return {}

    try:
        return get_flattened_config(discovered_config)
    except ValueError as exc:
        raise typer.BadParameter(f"Configuration error: {exc}") from exc


def resolve_report_format(value: ReportFormat | str | None) -> ReportFormat:
    if value is None:
        return ReportFormat.console

    if isinstance(value, ReportFormat):
        return value

    try:
        return ReportFormat(value)
    except ValueError as exc:
        valid_options = ", ".join(item.value for item in ReportFormat)
        raise typer.BadParameter(
            f"Invalid report format: {value}. "
            f"Valid options are: {valid_options}."
        ) from exc


def resolve_profile_mode(value: ProfileMode | str | None) -> ProfileMode:
    if value is None:
        return ProfileMode.deep

    if isinstance(value, ProfileMode):
        return value

    try:
        return ProfileMode(value)
    except ValueError as exc:
        valid_options = ", ".join(item.value for item in ProfileMode)
        raise typer.BadParameter(
            f"Invalid profiling mode: {value}. "
            f"Valid options are: {valid_options}."
        ) from exc


def resolve_output_path(
    output: str | None,
    output_dir: str | None,
    report: ReportFormat,
) -> str | None:
    if output and output_dir:
        raise typer.BadParameter("Use either --output or --output-dir, not both.")

    if report == ReportFormat.console:
        return None

    if output:
        return output

    if output_dir:
        return str(Path(output_dir) / resolve_default_name(report))

    return resolve_default_name(report)


def resolve_default_name(report: ReportFormat) -> str:
    default_names = {
        ReportFormat.json: "aniwa_report.json",
        ReportFormat.html: "aniwa_report.html",
        ReportFormat.excel: "aniwa_report.xlsx",
        ReportFormat.markdown: "aniwa_report.md",
        ReportFormat.pdf: "aniwa_report.pdf",
    }

    return default_names.get(report, "aniwa_report.txt")


def ensure_output_parent(output: str | None) -> None:
    if output is None:
        return

    Path(output).parent.mkdir(parents=True, exist_ok=True)


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024**2:
        return f"{size_bytes / 1024:.2f} KB"

    if size_bytes < 1024**3:
        return f"{size_bytes / 1024**2:.2f} MB"

    return f"{size_bytes / 1024**3:.2f} GB"


def build_command_used(
    path: str,
    report: ReportFormat,
    output: str | None,
    output_dir: str | None,
    mode: ProfileMode,
    include: str | None,
    exclude: str | None,
    template: str,
    config_file: str | None,
) -> str:
    command_parts = ["aniwa", path]

    if config_file:
        command_parts.extend(["--config", config_file])

    if report != ReportFormat.console:
        command_parts.extend(["--report", report.value])

    if output:
        command_parts.extend(["--output", output])

    if output_dir:
        command_parts.extend(["--output-dir", output_dir])

    if mode != ProfileMode.deep:
        command_parts.extend(["--mode", mode.value])

    if include:
        command_parts.extend(["--include", include])

    if exclude:
        command_parts.extend(["--exclude", exclude])

    if report in {ReportFormat.html, ReportFormat.pdf} and template != "default":
        command_parts.extend(["--template", template])

    return " ".join(command_parts)


def build_profile_metadata(
    dataset_path: Path,
    path: str,
    mode: ProfileMode,
    report: ReportFormat,
    output: str | None,
    output_dir: str | None,
    template: str,
    sections: set[ReportSection],
    include: str | None,
    exclude: str | None,
    duration_seconds: float,
    config_file: str | None,
) -> ProfileMetadata:
    include_sections = validate_sections(include)
    exclude_sections = validate_sections(exclude)

    return ProfileMetadata(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        aniwa_version=__version__,
        python_version=platform.python_version(),
        operating_system=f"{platform.system()} {platform.release()}",
        polars_version=pl.__version__,
        dataset_path=str(dataset_path),
        dataset_file_type=dataset_path.suffix.lower().lstrip(".").upper(),
        dataset_size=format_file_size(dataset_path.stat().st_size),
        profiling_mode=mode.value,
        report_format=report.value,
        report_template=template if report in {ReportFormat.html, ReportFormat.pdf} else None,
        included_sections=include_sections or sorted(section.value for section in sections),
        excluded_sections=exclude_sections,
        profiling_duration=f"{duration_seconds:.2f}s",
        command_used=build_command_used(
            path=path,
            report=report,
            output=output,
            output_dir=output_dir,
            mode=mode,
            include=include,
            exclude=exclude,
            template=template,
            config_file=config_file,
        ),
    )


@app.command()
def profile(
    path: str = typer.Argument(..., help="Path to dataset file."),
    config_file: str | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file.",
    ),
    report: ReportFormat | None = typer.Option(
        None,
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
    output_dir: str | None = typer.Option(
        None,
        "--output-dir",
        help="Output directory for generated report files.",
    ),
    mode: ProfileMode | None = typer.Option(
        None,
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
    ),
    template: str | None = typer.Option(
        None,
        "--template",
        "-t",
        help="Report template for HTML/PDF outputs. Options: default, clean, compact, enterprise, dark.",
    ),
):
    """
    Profile a dataset.
    """
    active_config = load_active_config(config_file)

    resolved_report = resolve_report_format(
        report if report is not None else active_config.get("report")
    )

    resolved_mode = resolve_profile_mode(
        mode if mode is not None else active_config.get("mode")
    )

    resolved_template = (
        template
        if template is not None
        else active_config.get("template", "default")
    )

    resolved_output = (
        output
        if output is not None
        else active_config.get("output")
    )

    resolved_output_dir = (
        output_dir
        if output_dir is not None
        else active_config.get("output_dir")
    )

    resolved_include = (
        include
        if include is not None
        else active_config.get("include")
    )

    resolved_exclude = (
        exclude
        if exclude is not None
        else active_config.get("exclude")
    )

    if include is not None:
        resolved_exclude = None

    if exclude is not None:
        resolved_include = None

    sections = resolve_sections(
        resolved_include,
        resolved_exclude,
    )

    final_output = resolve_output_path(
        output=resolved_output,
        output_dir=resolved_output_dir,
        report=resolved_report,
    )

    ensure_output_parent(final_output)
    TOTAL_STEPS = 5

    with Progress(  
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        progress.live.capture_stdout = True

        track_bar = progress.add_task(description="Profiling dataset...", total=TOTAL_STEPS)

        progress.update(track_bar, description=f"[yellow]Step 1/{TOTAL_STEPS}: Resolving sections...")
        time.sleep(0.5)
        sections = resolve_sections(include, exclude)
        progress.update(track_bar, advance=1)

        progress.update(track_bar, description=f"[yellow]Step 2/{TOTAL_STEPS}: Resolving output path...")
        time.sleep(0.5)
        output = resolve_output_path(output, output_dir, report)

        dataset_path = Path(path)

        if not dataset_path.exists():
            raise typer.BadParameter(f"File does not exist: {path}")

        progress.update(track_bar, advance=1)
        start_time = time.perf_counter()
        progress.update(track_bar, description=f"[yellow]Step 3/{TOTAL_STEPS}: Reading dataset...")
        time.sleep(0.5)
        df = read_dataset(path)
    
    dataset_profile = profile_dataframe(
            df,
            mode=resolved_mode.value,
            sections=sections,
        )
        progress.update(track_bar, advance=1)
        duration_seconds = time.perf_counter() - start_time

        progress.update(track_bar, description=f"[yellow]Step 4/{TOTAL_STEPS}: Building metadata...")
        time.sleep(0.5)
        dataset_profile.metadata = build_profile_metadata(
            dataset_path=dataset_path,
            path=path,
            mode=resolved_mode,
            report=resolved_report,
            output=final_output if resolved_output else None,
        output_dir=resolved_output_dir,
            template=resolved_template,
            sections=sections,
            include=resolved_include,
            exclude=resolved_exclude,
            duration_seconds=duration_seconds,
            config_file=config_file,
    )
        progress.update(track_bar, advance=1)
        progress.update(track_bar, description=f"[yellow]Step 5/{TOTAL_STEPS}: Generating report...")
        time.sleep(0.5)
        if resolved_report == ReportFormat.console:
            render_console_report(dataset_profile)

        if resolved_report == ReportFormat.json:
            json_output = render_json_report(dataset_profile, final_output)

            if final_output:
                progress.console.print(f"JSON report written to {final_output}")
            else:
                progress.console.print(json_output)

        if resolved_report == ReportFormat.html:
            try:
                render_html_report(dataset_profile, final_output, template=resolved_template)
            except ValueError as exc:
                raise typer.BadParameter(str(exc)) from exc

            progress.console.print(f"HTML report written to {final_output}")

        if resolved_report == ReportFormat.excel:
            try:
                render_excel_report(dataset_profile, final_output)
            except ValueError as exc:
                raise typer.BadParameter(str(exc)) from exc

            progress.console.print(f"Excel report written to {final_output}")

        if resolved_report == ReportFormat.markdown:
            markdown_output = render_markdown_report(dataset_profile, final_output)

            if final_output:
                progress.console.print(f"Markdown report written to {final_output}")
            else:
                progress.console.print(markdown_output)


        if resolved_report == ReportFormat.pdf:
            try:
                render_pdf_report(dataset_profile, final_output, template=resolved_template)
            except ValueError as exc:
                raise typer.BadParameter(str(exc)) from exc

            progress.console.print(f"PDF report written to {output}")
        progress.update(track_bar, advance=1, description=f"[green][SUCCESS] All steps completed!")
        return