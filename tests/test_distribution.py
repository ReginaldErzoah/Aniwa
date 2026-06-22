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
        sections={
            ReportSection.schema,
            ReportSection.statistics,
            ReportSection.charts,
        }
    )

    salary = profile.columns[0]

    assert salary.numeric_stats is not None
    assert salary.numeric_stats.histogram is not None

    histogram = salary.numeric_stats.histogram

    assert len(histogram.bins) > 0
    assert len(histogram.counts) > 0
    assert sum(histogram.counts) == 5