import json
import pathlib
from typing import Any, cast

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # TOML support unavailable


SUPPORTED_CONFIG_EXTENSIONS = {
    ".yaml",
    ".yml",
    ".toml",
    ".json",
}


def load_config(file_path: str) -> dict[str, Any]:
    path = pathlib.Path(file_path)

    if not path.exists():
        raise ValueError(f"Configuration file not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_CONFIG_EXTENSIONS:
        raise ValueError(
            "Unsupported configuration file type. "
            "Supported types are: .yaml, .yml, .toml, .json."
        )

    try:
        return _read_config(path, suffix)
    except Exception as exc:
        raise ValueError(f"Error parsing config file '{file_path}': {exc}") from exc


def _read_config(path: pathlib.Path, suffix: str) -> dict[str, Any]:
    if suffix == ".json":
        with path.open(encoding="utf-8") as file:
            data = json.load(file) or {}
        return _ensure_dict(data, path)

    if suffix == ".toml":
        if tomllib is None:
            raise ValueError("Install 'tomli' (or Python 3.11+) to use TOML configs.")

        with path.open("rb") as file:
            data = tomllib.load(file) or {}

        return _ensure_dict(data, path)

    if suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise ValueError("Install 'PyYAML' to use YAML configs.") from exc

        with path.open(encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}

        return _ensure_dict(data, path)

    raise ValueError("Unsupported configuration file type.")


def _ensure_dict(data: Any, path: pathlib.Path) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(
            f"Configuration file '{path}' must contain a top-level object."
        )
    return cast(dict[str, Any], data)


def get_flattened_config(file_path: str) -> dict[str, Any]:
    """Load and flatten a configuration file."""
    try:
        raw = load_config(file_path)
    except ValueError as e:
        if "not found" in str(e).lower():
            return {}
        raise

    if not raw:
        return {}

    flattened: dict[str, Any] = {}

    # Core mode
    if "mode" in raw:
        flattened["mode"] = raw["mode"]

    # Report config
    report = raw.get("report")
    if isinstance(report, dict):
        if "format" in report:
            flattened["report"] = report["format"]
        if "template" in report:
            flattened["template"] = report["template"]
        if "output" in report:
            flattened["output"] = report["output"]
        if "output_dir" in report:
            flattened["output_dir"] = report["output_dir"]

    # Sections
    sections = raw.get("sections")
    if isinstance(sections, dict):
        include = sections.get("include")
        exclude = sections.get("exclude")

        if include is not None and exclude is not None:
            raise ValueError(
                "Use either sections.include or sections.exclude, not both."
            )

        if isinstance(include, list):
            flattened["include"] = ",".join(map(str, include))

        if isinstance(exclude, list):
            flattened["exclude"] = ",".join(map(str, exclude))

    # verbosity support (NEW)
    if "verbosity" in raw:
        flattened["verbosity"] = raw["verbosity"]

    return flattened