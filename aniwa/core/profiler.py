import polars as pl
from typing import Callable, Optional

from aniwa.models.enums import ReportSection
from aniwa.models.profile import (
    ColumnProfile,
    DatasetProfile,
    DatasetSummary,
    HistogramData,
    Insight,
    NumericStats,
    QualityProfile,
)
from aniwa.utils.progress import ProgressTracker
from aniwa.utils.logging import get_logger, log_debug, log_verbose, log_info


NUMERIC_DTYPES = {
    pl.Int8,
    pl.Int16,
    pl.Int32,
    pl.Int64,
    pl.UInt8,
    pl.UInt16,
    pl.UInt32,
    pl.UInt64,
    pl.Float32,
    pl.Float64,
}


def profile_dataframe(
    df: pl.DataFrame,
    mode: str = "deep",
    sections: set[ReportSection] | None = None,
    verbose: bool = False,
) -> DatasetProfile:
    """Profile a DataFrame with optional progress tracking.
    
    Args:
        df: Polars DataFrame to profile
        mode: Profiling mode ("fast" or "deep")
        sections: Report sections to include
        verbose: Enable detailed progress output
    
    Returns:
        DatasetProfile containing all profiling results
    """
    if sections is None:
        sections = set(ReportSection)

    rows = df.height
    column_count = df.width
    
    # Get logger instance
    logger = get_logger()
    
    # Log debug information
    log_debug("Starting profile_dataframe", {
        "mode": mode,
        "sections": [s.value for s in sections],
        "rows": rows,
        "columns": column_count,
        "verbose": verbose,
    })
    
    # Initialize progress tracker
    tracker = ProgressTracker(verbose=verbose)

    summary = None
    if ReportSection.summary in sections:
        log_verbose("Generating dataset summary")
        with tracker.stage("Generating dataset summary"):
            summary = DatasetSummary(
                rows=rows,
                columns=column_count,
            )
            log_debug("Dataset summary generated", {
                "rows": summary.rows,
                "columns": summary.columns,
            })

    analysis_columns = None
    if _needs_column_analysis(sections):
        log_verbose("Starting column analysis")
        with tracker.stage(
            "Analyzing columns", 
            total_steps=len(df.columns) if verbose else None
        ) as progress_callback:
            analysis_columns = _profile_columns(
                df=df,
                rows=rows,
                mode=mode,
                include_statistics=ReportSection.statistics in sections,
                progress_callback=progress_callback,
                verbose=verbose,
            )
            log_debug(f"Column analysis complete. Processed {len(analysis_columns)} columns")

    displayed_columns = None
    if _should_display_columns(sections):
        displayed_columns = analysis_columns or _profile_columns(
            df=df,
            rows=rows,
            mode=mode,
            include_statistics=ReportSection.statistics in sections,
            verbose=verbose,
        )
        log_debug(f"Prepared {len(displayed_columns)} columns for display")

    duplicate_rows = 0
    duplicate_percent = 0.0

    if _needs_duplicate_analysis(sections):
        log_verbose("Detecting duplicate rows")
        with tracker.stage("Detecting duplicate rows"):
            duplicate_rows = rows - df.unique().height
            duplicate_percent = round((duplicate_rows / rows) * 100, 2) if rows else 0.0
            log_debug(f"Duplicate detection complete", {
                "duplicate_rows": duplicate_rows,
                "duplicate_percent": duplicate_percent,
            })

    quality = None
    if ReportSection.quality in sections:
        log_verbose("Building quality profile")
        with tracker.stage("Building quality profile"):
            quality = QualityProfile(
                duplicate_rows=duplicate_rows,
                duplicate_percent=duplicate_percent,
            )
            log_debug("Quality profile built")

    insights = None
    if ReportSection.insights in sections:
        log_verbose("Generating insights")
        with tracker.stage("Generating insights"):
            insights = generate_insights(
                columns=analysis_columns or [],
                duplicate_rows=duplicate_rows,
                total_rows=rows,
            )
            log_debug(f"Generated {len(insights)} insights")

    # Show timing summary if verbose
    if verbose:
        tracker.show_timing_summary()
    
    log_debug("Profile_dataframe completed successfully")

    return DatasetProfile(
        summary=summary,
        columns=displayed_columns,
        quality=quality,
        insights=insights,
    )


def _needs_column_analysis(sections: set[ReportSection]) -> bool:
    return any(
        section in sections
        for section in {
            ReportSection.schema,
            ReportSection.statistics,
            ReportSection.insights,
            ReportSection.charts,
        }
    )


def _should_display_columns(sections: set[ReportSection]) -> bool:
    return any(
        section in sections
        for section in {
            ReportSection.schema,
            ReportSection.statistics,
            ReportSection.charts,
        }
    )


def _needs_duplicate_analysis(sections: set[ReportSection]) -> bool:
    return any(
        section in sections
        for section in {
            ReportSection.quality,
            ReportSection.insights,
            ReportSection.charts,
        }
    )


def _profile_columns(
    df: pl.DataFrame,
    rows: int,
    mode: str,
    include_statistics: bool,
    progress_callback: Optional[Callable[[int], None]] = None,
    verbose: bool = False,
) -> list[ColumnProfile]:
    """Profile all columns with optional progress callback.
    
    Args:
        df: Polars DataFrame
        rows: Total row count
        mode: Profiling mode
        include_statistics: Whether to compute numeric statistics
        progress_callback: Optional callback to advance progress bar
        verbose: Enable detailed progress output
    
    Returns:
        List of ColumnProfile objects
    """
    column_profiles: list[ColumnProfile] = []
    total_columns = len(df.columns)
    
    # Get logger
    logger = get_logger()
    
    # Count numeric columns for debug
    numeric_columns_count = 0
    if include_statistics and mode == "deep":
        for col in df.columns:
            if df[col].dtype in NUMERIC_DTYPES:
                numeric_columns_count += 1
        log_debug(f"Found {numeric_columns_count} numeric columns for statistics computation")

    for idx, col in enumerate(df.columns):
        series = df[col]
        is_numeric = series.dtype in NUMERIC_DTYPES

        # Log progress for debug mode
        if verbose and idx % 10 == 0:  # Log every 10 columns to avoid spam
            log_debug(f"Processing column {idx+1}/{total_columns}: {col}")

        null_count = series.null_count()
        null_percent = round((null_count / rows) * 100, 2) if rows else 0.0
        unique_count = series.n_unique()

        numeric_stats = None

        if include_statistics and mode == "deep" and is_numeric:
            # Compute statistics
            if verbose:
                from rich.console import Console
                console = Console()
                console.print(f"[dim]    Computing stats for {col}...[/dim]")
            
            try:
                numeric_stats = NumericStats(
                    min=_safe_float(series.min()),
                    max=_safe_float(series.max()),
                    mean=_safe_float(series.mean()),
                    median=_safe_float(series.median()),
                    std=_safe_float(series.std()),
                    histogram=_generate_histogram(series),
                )
                
                if verbose:
                    console.print(f"[dim]    ✓ Stats for {col} complete[/dim]")
                
                log_debug(f"Statistics computed for column: {col}", {
                    "min": numeric_stats.min,
                    "max": numeric_stats.max,
                    "mean": numeric_stats.mean,
                    "median": numeric_stats.median,
                    "std": numeric_stats.std,
                } if numeric_stats else None)
                
            except Exception as e:
                log_debug(f"Error computing statistics for column {col}: {str(e)}")
                # Continue with None stats instead of failing

        column_profiles.append(
            ColumnProfile(
                name=col,
                dtype=str(series.dtype),
                null_count=null_count,
                null_percent=null_percent,
                unique_count=unique_count,
                numeric_stats=numeric_stats,
            )
        )
        
        # Advance progress bar if callback provided
        if progress_callback:
            progress_callback(1)

    log_debug(f"Column profiling complete. Processed {len(column_profiles)} columns")
    return column_profiles


def _safe_float(value: object) -> float | None:
    """Safely convert value to float."""
    if value is None:
        return None

    try:
        # Handle NaN values
        if hasattr(value, 'is_nan') and callable(getattr(value, 'is_nan')):
            if value.is_nan():
                return None
        
        # Handle infinite values
        if hasattr(value, 'is_infinite') and callable(getattr(value, 'is_infinite')):
            if value.is_infinite():
                return None
                
        return round(float(value), 4)
    except (TypeError, ValueError, OverflowError):
        return None


def _generate_histogram(
    series: pl.Series,
    bins: int = 10,
) -> HistogramData | None:
    """
    Generate histogram distribution data for numeric columns.
    """

    try:
        values = series.drop_nulls()

        if values.len() == 0:
            return None

        min_value = float(values.min())
        max_value = float(values.max())

        if min_value == max_value:
            return HistogramData(
                bins=[min_value],
                counts=[values.len()],
            )

        step = (max_value - min_value) / bins

        edges = [
            round(min_value + (step * i), 4)
            for i in range(bins + 1)
        ]

        counts = [0] * bins

        for value in values:
            index = int((float(value) - min_value) / step)

            if index == bins:
                index -= 1

            counts[index] += 1

        return HistogramData(
            bins=edges,
            counts=counts,
        )

    except Exception:
        return None
    

def generate_insights(
    columns: list[ColumnProfile],
    duplicate_rows: int,
    total_rows: int,
) -> list[Insight]:
    """Generate insights from profiling data."""
    insights: list[Insight] = []
    logger = get_logger()
    
    log_debug("Generating insights from profiling data", {
        "total_columns": len(columns),
        "total_rows": total_rows,
        "duplicate_rows": duplicate_rows,
    })

    if duplicate_rows > 0:
        insights.append(
            Insight(
                level="warning",
                message=f"{duplicate_rows} duplicate rows detected.",
            )
        )
        log_debug(f"Added duplicate rows insight: {duplicate_rows} rows")

    for col in columns:
        column_name = col.name.lower()

        # Null value insights
        if col.null_percent >= 75:
            insights.append(
                Insight(
                    level="critical",
                    message=(
                        f"Column '{col.name}' is extremely sparse "
                        f"with {col.null_percent}% null values."
                    ),
                )
            )
            log_debug(f"Added critical null insight for {col.name}: {col.null_percent}%")

        elif col.null_percent >= 40:
            insights.append(
                Insight(
                    level="warning",
                    message=(
                        f"Column '{col.name}' contains "
                        f"{col.null_percent}% null values."
                    ),
                )
            )
            log_debug(f"Added warning null insight for {col.name}: {col.null_percent}%")

        # Uniqueness insights
        if col.unique_count == 1:
            insights.append(
                Insight(
                    level="warning",
                    message=f"Column '{col.name}' contains only one unique value.",
                )
            )
            log_debug(f"Added constant column insight for {col.name}")

        if (
            col.unique_count == total_rows
            and total_rows > 0
            and "name" not in column_name
        ):
            insights.append(
                Insight(
                    level="info",
                    message=f"Column '{col.name}' may be a unique identifier.",
                )
            )
            log_debug(f"Added unique identifier insight for {col.name}")

        if total_rows > 0:
            cardinality_ratio = col.unique_count / total_rows

            if cardinality_ratio >= 0.9 and total_rows > 20:
                insights.append(
                    Insight(
                        level="info",
                        message=f"Column '{col.name}' has very high cardinality.",
                    )
                )
                log_debug(f"Added high cardinality insight for {col.name}: {cardinality_ratio:.2%}")

        # PII detection insights
        pii_keywords = [
            "email", "phone", "mobile", "ssn", "passport", 
            "card", "credit", "address", "zip", "postal",
            "birth", "social", "security", "tax", "bank"
        ]

        if any(keyword in column_name for keyword in pii_keywords):
            insights.append(
                Insight(
                    level="warning",
                    message=f"Column '{col.name}' may contain sensitive information.",
                )
            )
            log_debug(f"Added PII insight for {col.name}")

        # Numeric insights
        if col.numeric_stats:
            stats = col.numeric_stats

            if stats.min is not None and stats.min < 0:
                insights.append(
                    Insight(
                        level="info",
                        message=f"Column '{col.name}' contains negative values.",
                    )
                )
                log_debug(f"Added negative values insight for {col.name}: min={stats.min}")

            if (
                stats.mean is not None
                and stats.std is not None
                and stats.mean != 0
            ):
                variability_ratio = abs(stats.std / stats.mean)

                if variability_ratio > 2:
                    insights.append(
                        Insight(
                            level="info",
                            message=f"Column '{col.name}' shows high variability.",
                        )
                    )
                    log_debug(f"Added high variability insight for {col.name}: ratio={variability_ratio:.2f}")

    log_debug(f"Insight generation complete. Total insights: {len(insights)}")
    return insights