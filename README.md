# Aniwa

<p align="center">
  <picture>
    <source
      media="(prefers-color-scheme: dark)"
      srcset="https://raw.githubusercontent.com/ReginaldErzoah/Aniwa/main/docs/assets/aniwa-logo-dark.png"
    />
    <source
      media="(prefers-color-scheme: light)"
      srcset="https://raw.githubusercontent.com/ReginaldErzoah/Aniwa/main/docs/assets/aniwa-logo-light.png"
    />
    <img
      src="https://raw.githubusercontent.com/ReginaldErzoah/Aniwa/main/docs/assets/aniwa-logo.png"
      width="400"
      alt="Aniwa Logo"
    />
  </picture>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue" />
  <img src="https://img.shields.io/badge/license-MIT-green" />
  <img src="https://img.shields.io/badge/version-0.1.1-blue" />
</p>

> **See your data clearly.**

## What is Aniwa?

Aniwa is an open-source universal dataset profiling and intelligence tool for developers, analysts, data engineers, researchers, and modern data teams.

Aniwa helps users quickly understand datasets through:

- schema profiling
- data quality analysis
- statistical summaries
- intelligent insights
- rich terminal reports
- shareable reports
- configurable profiling workflows

Whether you're working with CSV files, Excel spreadsheets, JSON datasets, or Parquet files, Aniwa provides a fast and elegant way to inspect, understand, and trust your data.


Full documentation available here:
https://reginalderzoah.github.io/Aniwa/


---

## Why Aniwa?

Modern data workflows constantly involve:

```text
unknown datasets
```

Before trusting a dataset, teams need to answer questions like:

- What columns exist?
- What data types are present?
- Are there missing values?
- Are there duplicates?
- Are there suspicious patterns?
- Which columns may contain IDs or sensitive information?
- Is the dataset healthy?

Aniwa makes answering those questions:

```text
fast, intelligent, and developer-friendly
```

---

## Features

### Universal Dataset Support

Aniwa currently supports:

- CSV
- Excel (.xlsx/.xls)
- JSON
- Parquet

Future releases are planned to support:

- PostgreSQL
- MySQL
- DuckDB
- BigQuery
- Snowflake

---

### Core Profiling

Aniwa currently provides:

#### Dataset Summary

- row counts
- column counts
- dataset size analysis

#### Schema Profiling

- type inference
- schema overview
- mixed type detection

#### Data Quality Analysis

- null analysis
- duplicate detection
- uniqueness analysis
- sparse column detection

#### Statistical Profiling

- minimum values
- maximum values
- mean
- median
- standard deviation

#### Intelligent Insights

- possible ID detection
- high-cardinality warnings
- sparse column warnings
- suspicious quality patterns

---

### Reporting

Aniwa currently supports:

- Rich terminal reports
- JSON reports
- HTML reports

Upcoming releases are planned to include:

- Markdown reports
- Excel reports
- PDF reports
- charts
- report templates

---

## Quick Installation

Install Aniwa from PyPI:

```bash
pip install aniwa
```

Verify installation:

```bash
aniwa --help
```

Upgrade Aniwa:

```bash
pip install --upgrade aniwa
```

---

## Quick Start

Profile a dataset:

```bash
aniwa profile customers.csv
```

Generate a JSON report:

```bash
aniwa profile customers.csv --report json --output profile.json
```

Generate an HTML report:

```bash
aniwa profile customers.csv --report html --output profile.html
```

Run lightweight profiling:

```bash
aniwa profile customers.csv --mode fast
```

Run full profiling:

```bash
aniwa profile customers.csv --mode deep
```

---

## Configuration Files

Aniwa supports configuration-driven workflows.

Supported config formats:

- YAML
- TOML
- JSON

Aniwa automatically searches for:

```text
aniwa.yaml
aniwa.yml
aniwa.toml
aniwa.json
```

Example:

```yaml
mode: deep

report:
  format: html
  output_dir: reports/

sections:
  include:
    - summary
    - schema
    - statistics
    - insights
```

Use a custom config file:

```bash
aniwa profile customers.csv --config config.yaml
```

---

# Report Sections

Aniwa supports configurable report sections.

Current sections include:

- summary
- schema
- quality
- statistics
- insights

Example:

```bash
aniwa profile customers.csv --include summary,statistics
```

Exclude sections:

```bash
aniwa profile customers.csv --exclude statistics
```

---

## Example Console Output

```text
┌──────────────────────────────┐
│      Aniwa Dataset Profile   │
├──────────────────────────────┤
│ Rows: 5                      │
│ Columns: 5                   │
│ Duplicate Rows: 1            │
└──────────────────────────────┘
```

---

## Documentation

Aniwa now includes a full documentation system.

Full documentation available here:
https://reginalderzoah.github.io/Aniwa/

Documentation includes:

- getting started guides
- architecture documentation
- developer guides
- release notes
- roadmap
- philosophy

View documentation locally with MkDocs:

```bash
mkdocs serve
```

Build documentation:

```bash
mkdocs build
```

Documentation structure:

```text
docs/
├── index.md
├── roadmap.md
├── philosophy.md
├── getting-started/
├── developer-guide/
└── release-notes/
```

---

## Installation for Development

Clone the repository:

```bash
git clone https://github.com/ReginaldErzoah/Aniwa.git
cd Aniwa
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment:

## Windows

```bash
source .venv/Scripts/activate
```

## macOS/Linux

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install Aniwa locally:

```bash
pip install -e .
```

---

## Architecture

Aniwa currently follows a modular layered architecture:

```text
CLI
-> Configuration
-> Readers
-> Profiling Engine
-> Models
-> Reports
```

This architecture prioritizes:

- modularity
- maintainability
- scalability
- contributor friendliness

---

## Project Structure

```text
Aniwa/
│
├── aniwa/
│   ├── cli.py
│   ├── config/
│   ├── core/
│   ├── io/
│   ├── models/
│   ├── reports/
│   ├── templates/
│   └── utils/
│
├── docs/
├── tests/
├── examples/
│
├── README.md
├── CONTRIBUTING.md
├── SPRINT.md
├── mkdocs.yml
├── pyproject.toml
└── requirements.txt
```

---

## Roadmap

### v0.1.x - Foundation

- universal dataset profiling
- reporting systems
- configuration workflows
- modular architecture
- developer-first UX

### v0.2.x - Better User Experience

Planned features:

- Better HTML with charts.
- Better report templates.
- Report modes and presets.
- Better output management.
- Metadata
- Incldue & exclude sections.
- Config file supports (yml, json & toml).
- Improved documentation.

### v0.3.x - Intelligence

Planned features:

- correlation analysis
- anomaly detection
- semantic profiling
- improved insights

### v0.4.x - Universal Connectivity

Planned features:

- PostgreSQL support
- MySQL support
- DuckDB support
- BigQuery support
- profiling history
- snapshot management

### v0.5.x - Extensibility

Planned features:

- plugin system
- custom profiling modules
- community extensions

### v0.6.x - AI Intelligence

Planned features:

- dataset summarization
- semantic understanding
- AI-assisted recommendations
- anomaly explanations

---

## Philosophy

Aniwa is built around several core principles:

- universal
- developer-first
- fast
- modular
- intelligent
- beautiful
- automation-friendly

The long-term goal is to build:

```text
universal data intelligence infrastructure
```

For deeper architectural and ecosystem thinking, see:

```text
docs/philosophy.md
docs/roadmap.md
```

---

## Contributing

Contributions are welcome.

See:

- CONTRIBUTING.md
- SPRINT.md
- docs/developer-guide/

for:

- local development
- testing workflows
- architecture guidance
- release workflows
- contributor standards

---

## Support

If you find this project useful:

- star the repository
- Share repo with friends
- Contribute to making this project better solving open issues
- Recommendations can also be sent to maintainer