import polars as pl

from aniwa.core.profiler import profile_dataframe
from aniwa.models.enums import ReportSection


def test_profile_dataframe_summary():
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Ama", "Kofi", "Yaw"],
        }
    )

    profile = profile_dataframe(df)

    assert profile.summary is not None
    assert profile.summary.rows == 3
    assert profile.summary.columns == 2


def test_profile_dataframe_nulls():
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "email": ["a@test.com", None, None],
        }
    )

    profile = profile_dataframe(df)

    assert profile.columns is not None

    email_profile = next(col for col in profile.columns if col.name == "email")

    assert email_profile.null_count == 2
    assert email_profile.null_percent == 66.67


def test_duplicate_detection():
    df = pl.DataFrame(
        {
            "id": [1, 1, 2],
            "name": ["Ama", "Ama", "Kofi"],
        }
    )

    profile = profile_dataframe(df)

    assert profile.quality is not None
    assert profile.quality.duplicate_rows == 1


def test_numeric_statistics():
    df = pl.DataFrame(
        {
            "revenue": [100, 200, 300, 400],
            "name": ["Ama", "Kofi", "Yaw", "Akosua"],
        }
    )

    profile = profile_dataframe(df)

    assert profile.columns is not None

    revenue_profile = next(
        col for col in profile.columns if col.name == "revenue"
    )

    assert revenue_profile.numeric_stats is not None
    assert revenue_profile.numeric_stats.min == 100.0
    assert revenue_profile.numeric_stats.max == 400.0
    assert revenue_profile.numeric_stats.mean == 250.0
    assert revenue_profile.numeric_stats.median == 250.0


def test_histogram_generation_in_deep_mode():
    df = pl.DataFrame(
        {
            "revenue": [100, 200, 300, 400, 500],
        }
    )

    profile = profile_dataframe(
        df,
        mode="deep",
        sections={ReportSection.statistics},
    )

    revenue_profile = next(
        col for col in profile.columns if col.name == "revenue"
    )

    assert revenue_profile.numeric_stats is not None
    assert revenue_profile.numeric_stats.histogram is not None
    assert len(revenue_profile.numeric_stats.histogram.bins) > 0
    assert len(revenue_profile.numeric_stats.histogram.counts) > 0


def test_histogram_skipped_in_fast_mode():
    df = pl.DataFrame(
        {
            "revenue": [100, 200, 300, 400, 500],
        }
    )

    profile = profile_dataframe(
        df,
        mode="fast",
        sections={ReportSection.statistics},
    )

    revenue_profile = next(
        col for col in profile.columns if col.name == "revenue"
    )

    # fast mode should NOT generate histogram
    assert revenue_profile.numeric_stats is None or revenue_profile.numeric_stats.histogram is None


def test_profile_dataframe_can_include_only_summary():
    df = pl.DataFrame({"id": [1, 2, 3]})

    profile = profile_dataframe(
        df,
        sections={ReportSection.summary},
    )

    assert profile.summary is not None
    assert profile.summary.rows == 3
    assert profile.summary.columns == 1
    assert profile.columns is None
    assert profile.quality is None
    assert profile.insights is None


def test_profile_dataframe_can_include_only_schema():
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Ama", "Kofi", "Yaw"],
        }
    )

    profile = profile_dataframe(
        df,
        sections={ReportSection.schema},
    )

    assert profile.summary is None
    assert profile.columns is not None
    assert profile.quality is None
    assert profile.insights is None

    assert len(profile.columns) == 2
    assert all(col.numeric_stats is None for col in profile.columns)


def test_profile_dataframe_can_include_only_quality():
    df = pl.DataFrame(
        {
            "id": [1, 1, 2],
            "name": ["Ama", "Ama", "Kofi"],
        }
    )

    profile = profile_dataframe(
        df,
        sections={ReportSection.quality},
    )

    assert profile.summary is None
    assert profile.columns is None
    assert profile.quality is not None
    assert profile.insights is None
    assert profile.quality.duplicate_rows == 1


def test_profile_dataframe_can_include_only_statistics():
    df = pl.DataFrame(
        {
            "revenue": [100, 200, 300],
            "name": ["Ama", "Kofi", "Yaw"],
        }
    )

    profile = profile_dataframe(
        df,
        sections={ReportSection.statistics},
    )

    assert profile.summary is None
    assert profile.columns is not None
    assert profile.quality is None
    assert profile.insights is None

    revenue_profile = next(
        col for col in profile.columns if col.name == "revenue"
    )

    assert revenue_profile.numeric_stats is not None
    assert revenue_profile.numeric_stats.mean == 200.0


def test_profile_dataframe_can_include_only_insights():
    df = pl.DataFrame(
        {
            "id": [1, 1, 2],
            "email": ["a@test.com", None, None],
        }
    )

    profile = profile_dataframe(
        df,
        sections={ReportSection.insights},
    )

    assert profile.summary is None
    assert profile.columns is None
    assert profile.quality is None
    assert profile.insights is not None
    assert len(profile.insights) > 0


def test_profile_dataframe_charts_requires_columns_and_duplicate_analysis():
    df = pl.DataFrame(
        {
            "id": [1, 1, 2],
            "name": ["Ama", "Ama", "Kofi"],
        }
    )

    profile = profile_dataframe(
        df,
        sections={ReportSection.charts},
    )

    assert profile.summary is None
    assert profile.columns is not None
    assert profile.quality is None
    assert profile.insights is None


def test_profile_dataframe_can_exclude_statistics():
    df = pl.DataFrame({"revenue": [100, 200, 300]})

    profile = profile_dataframe(
        df,
        sections={
            ReportSection.summary,
            ReportSection.schema,
            ReportSection.quality,
            ReportSection.insights,
        },
    )

    assert profile.columns is not None

    revenue_profile = next(
        col for col in profile.columns if col.name == "revenue"
    )

    assert revenue_profile.numeric_stats is None


def test_profile_dataframe_fast_mode_skips_numeric_statistics():
    df = pl.DataFrame({"revenue": [100, 200, 300]})

    profile = profile_dataframe(
        df,
        mode="fast",
        sections={ReportSection.statistics},
    )

    assert profile.columns is not None

    revenue_profile = next(
        col for col in profile.columns if col.name == "revenue"
    )

    assert revenue_profile.numeric_stats is None