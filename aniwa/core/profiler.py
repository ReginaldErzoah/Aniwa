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
from aniwa.utils.logging import get_logger, log_debug, log_verbose


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

    if sections is None:
        sections = set(ReportSection)

    rows = df.height
    column_count = df.width

    tracker = ProgressTracker(verbose=verbose)

    summary = None
    if ReportSection.summary in sections:
        summary = DatasetSummary(rows=rows, columns=column_count)

    analysis_columns = None
    if _needs_column_analysis(sections):
        with tracker.stage("Analyzing columns") as progress:
            analysis_columns = _profile_columns(
                df=df,
                rows=rows,
                mode=mode,
                include_statistics=ReportSection.statistics in sections,
                progress_callback=progress,
                verbose=verbose,
            )

    displayed_columns = None
    if _should_display_columns(sections):
        displayed_columns = analysis_columns or _profile_columns(
            df=df,
            rows=rows,
            mode=mode,
            include_statistics=ReportSection.statistics in sections,
            verbose=verbose,
        )

    duplicate_rows = 0
    duplicate_percent = 0.0

    if _needs_duplicate_analysis(sections):
        duplicate_rows = rows - df.unique().height
        duplicate_percent = round((duplicate_rows / rows) * 100, 2) if rows else 0.0

    quality = None
    if ReportSection.quality in sections:
        quality = QualityProfile(
            duplicate_rows=duplicate_rows,
            duplicate_percent=duplicate_percent,
        )

    insights = None
    if ReportSection.insights in sections:
        insights = generate_insights(
            columns=analysis_columns or [],
            duplicate_rows=duplicate_rows,
            total_rows=rows,
        )

    return DatasetProfile(
        summary=summary,
        columns=displayed_columns,
        quality=quality,
        insights=insights,
    )


# ----------------------------
# Column analysis
# ----------------------------

def _profile_columns(
    df: pl.DataFrame,
    rows: int,
    mode: str,
    include_statistics: bool,
    progress_callback: Optional[Callable[[int], None]] = None,
    verbose: bool = False,
) -> list[ColumnProfile]:

    column_profiles: list[ColumnProfile] = []

    for idx, col in enumerate(df.columns):
        series = df[col]
        is_numeric = series.dtype in NUMERIC_DTYPES

        null_count = series.null_count()
        null_percent = round((null_count / rows) * 100, 2) if rows else 0.0
        unique_count = series.n_unique()

        numeric_stats = None

        if include_statistics and mode == "deep" and is_numeric:
            numeric_stats = NumericStats(
                min=_safe_float(series.min()),
                max=_safe_float(series.max()),
                mean=_safe_float(series.mean()),
                median=_safe_float(series.median()),
                std=_safe_float(series.std()),
                histogram=_generate_histogram(series),
            )

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

        if progress_callback:
            progress_callback(1)

    return column_profiles


# ----------------------------
# Safe conversion
# ----------------------------

def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        if hasattr(value, "is_nan") and value.is_nan():
            return None
        return round(float(value), 4)
    except Exception:
        return None


# ----------------------------
# Histogram generation
# ----------------------------

def _generate_histogram(series: pl.Series, bins: int = 10) -> HistogramData | None:

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
                bin_count=1,
                bin_method="constant",
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
            bin_count=bins,
            bin_method="equal_width",
        )

    except Exception:
        return None


# ----------------------------
# Insights
# ----------------------------

def generate_insights(
    columns: list[ColumnProfile],
    duplicate_rows: int,
    total_rows: int,
) -> list[Insight]:

    insights: list[Insight] = []

    if duplicate_rows > 0:
        insights.append(
            Insight(
                level="warning",
                message=f"{duplicate_rows} duplicate rows detected.",
            )
        )

    for col in columns:
        name_lower = col.name.lower()

        if col.null_percent >= 75:
            insights.append(
                Insight(
                    level="critical",
                    message=f"{col.name} is extremely sparse ({col.null_percent}%).",
                )
            )

        elif col.null_percent >= 40:
            insights.append(
                Insight(
                    level="warning",
                    message=f"{col.name} has {col.null_percent}% missing values.",
                )
            )

        if col.unique_count == 1:
            insights.append(
                Insight(
                    level="warning",
                    message=f"{col.name} has only one unique value.",
                )
            )

        if total_rows > 0 and col.unique_count == total_rows:
            insights.append(
                Insight(
                    level="info",
                    message=f"{col.name} looks like a unique identifier.",
                )
            )

        if any(k in name_lower for k in ["email", "phone", "address", "card"]):
            insights.append(
                Insight(
                    level="warning",
                    message=f"{col.name} may contain sensitive data.",
                )
            )

        if col.numeric_stats:
            stats = col.numeric_stats

            if stats.min is not None and stats.min < 0:
                insights.append(
                    Insight(
                        level="info",
                        message=f"{col.name} contains negative values.",
                    )
                )

            if stats.mean and stats.std and stats.mean != 0:
                ratio = abs(stats.std / stats.mean)
                if ratio > 2:
                    insights.append(
                        Insight(
                            level="info",
                            message=f"{col.name} shows high variability.",
                        )
                    )

    return insights


# ----------------------------
# Section helpers
# ----------------------------

def _needs_column_analysis(sections: set[ReportSection]) -> bool:
    return any(s in sections for s in {
        ReportSection.schema,
        ReportSection.statistics,
        ReportSection.insights,
        ReportSection.charts,
    })


def _should_display_columns(sections: set[ReportSection]) -> bool:
    return any(s in sections for s in {
        ReportSection.schema,
        ReportSection.statistics,
        ReportSection.charts,
    })


def _needs_duplicate_analysis(sections: set[ReportSection]) -> bool:
    return any(s in sections for s in {
        ReportSection.quality,
        ReportSection.insights,
        ReportSection.charts,
    })