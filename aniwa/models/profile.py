from pydantic import BaseModel


class DatasetSummary(BaseModel):
    rows: int
    columns: int


class HistogramData(BaseModel):
    bins: list[float] = []
    counts: list[int] = []

    # Optional metadata for explainability / tuning
    bin_method: str | None = None
    bin_count: int | None = None


class NumericDistribution(BaseModel):
    histogram: HistogramData | None = None


class NumericStats(BaseModel):
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    median: float | None = None
    std: float | None = None

    # Histogram-based distribution (used for charts)
    distribution: NumericDistribution | None = None


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    null_count: int
    null_percent: float
    unique_count: int

    numeric_stats: NumericStats | None = None


class QualityProfile(BaseModel):
    duplicate_rows: int
    duplicate_percent: float


class Insight(BaseModel):
    level: str
    message: str


class ProfileMetadata(BaseModel):
    generated_at: str | None = None

    aniwa_version: str | None = None
    python_version: str | None = None
    operating_system: str | None = None
    polars_version: str | None = None

    dataset_path: str | None = None
    dataset_file_type: str | None = None
    dataset_size: str | None = None

    profiling_mode: str | None = None

    report_format: str | None = None
    report_template: str | None = None

    included_sections: list[str] | None = None
    excluded_sections: list[str] | None = None

    profiling_duration: str | None = None

    command_used: str | None = None


class DatasetProfile(BaseModel):
    summary: DatasetSummary | None = None
    columns: list[ColumnProfile] | None = None
    quality: QualityProfile | None = None
    insights: list[Insight] | None = None
    metadata: ProfileMetadata | None = None