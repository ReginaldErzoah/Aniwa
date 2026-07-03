import polars as pl

from aniwa.core.profiler import profile_dataframe
from aniwa.models.enums import ReportSection


def test_numeric_histogram_generation():

    df = pl.DataFrame(
        {
            "salary": [
                100,
                200,
                300,
                400,
                500,
            ]
        }
    )

    profile = profile_dataframe(
        df,
        mode="deep",
        sections={
            ReportSection.schema,
            ReportSection.statistics,
            ReportSection.charts,
        }
    )

    salary = next(col for col in profile.columns if col.name == "salary")

    assert salary.numeric_stats is not None
    assert salary.numeric_stats.histogram is not None

    histogram = salary.numeric_stats.histogram

    assert len(histogram.bins) > 0
    assert len(histogram.counts) > 0
    assert len(histogram.bins) == len(histogram.counts) + 1
    assert sum(histogram.counts) == 5


def test_histogram_respects_null_values():

    df = pl.DataFrame(
        {
            "salary": [100, 200, None, 400, 500]
        }
    )

    profile = profile_dataframe(
        df,
        mode="deep",
        sections={
            ReportSection.schema,
            ReportSection.statistics,
            ReportSection.charts,
        }
    )

    salary = next(col for col in profile.columns if col.name == "salary")

    histogram = salary.numeric_stats.histogram

    # histogram should ignore nulls internally
    assert sum(histogram.counts) == 4


def test_histogram_edge_case_constant_values():

    df = pl.DataFrame(
        {
            "score": [50, 50, 50, 50]
        }
    )

    profile = profile_dataframe(
        df,
        mode="deep",
        sections={
            ReportSection.schema,
            ReportSection.statistics,
            ReportSection.charts,
        }
    )

    score = next(col for col in profile.columns if col.name == "score")

    histogram = score.numeric_stats.histogram

    assert histogram is not None
    assert len(histogram.bins) == 2  # constant-case behavior
    assert len(histogram.counts) == 1
    assert histogram.counts[0] == 4


def test_histogram_not_generated_in_fast_mode():

    df = pl.DataFrame(
        {
            "salary": [100, 200, 300, 400, 500]
        }
    )

    profile = profile_dataframe(
        df,
        mode="fast",
        sections={ReportSection.statistics}
    )

    salary = next(col for col in profile.columns if col.name == "salary")

    # fast mode should not include histogram
    assert salary.numeric_stats is None or salary.numeric_stats.histogram is None