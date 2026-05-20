from pathlib import Path

from aniwa.models.profile import DatasetProfile
import csv
from io import StringIO

def render_csv_summary_report(profile: DatasetProfile, output: str | None = None) -> str:
    

    output_buffer = StringIO()
    writer = csv.writer(output_buffer)

    if profile.summary:
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Rows", profile.summary.rows])
        writer.writerow(["Columns", profile.summary.columns])
    if profile.quality:
        writer.writerow(["Duplicate Rows", profile.quality.duplicate_rows])
        writer.writerow(["Duplicate Percent", f"{profile.quality.duplicate_percent:.2f}%"])
    csv_content = output_buffer.getvalue()

    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(csv_content, encoding="utf-8", newline="")
        return f"CSV report written to {output}"

    return csv_content