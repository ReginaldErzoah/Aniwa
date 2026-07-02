import json
import pathlib
from typing import Any, cast

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


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
            raise ValueError("Install 'tomli' to use TOML configs.")

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

    raise ValueError(
        "Unsupported configuration file type. "
        "Supported types are: .yaml, .yml, .toml, .json."
    )


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

    # -------------------------
    # Core mode
    # -------------------------
    if "mode" in raw:
        mode = raw["mode"]

        if mode not in {"fast", "deep"}:
            raise ValueError(
                f"Invalid mode in config: {mode}. Use 'fast' or 'deep'."
            )

        flattened["mode"] = mode

    # -------------------------
    # Report config
    # -------------------------
    if "report" in raw:
        report = raw["report"]

        if not isinstance(report, dict):
            raise ValueError("Invalid config: 'report' must be an object.")

        if "format" in report:
            flattened["report"] = report["format"]

        if "template" in report:
            flattened["template"] = report["template"]

        if "output" in report:
            flattened["output"] = report["output"]

        if "output_dir" in report:
            flattened["output_dir"] = report["output_dir"]

    # -------------------------
    # Sections config (UPDATED SAFETY LAYER)
    # -------------------------
    if "sections" in raw:
        sections = raw["sections"]

        if not isinstance(sections, dict):
            raise ValueError("Invalid config: 'sections' must be an object.")

        include = sections.get("include")
        exclude = sections.get("exclude")

        if include is not None and exclude is not None:
            raise ValueError(
                "Invalid config: use either sections.include or sections.exclude, not both."
            )

        if include is not None:
            if not isinstance(include, list):
                raise ValueError("Invalid config: sections.include must be a list.")

            flattened["include"] = ",".join(str(s) for s in include)
            flattened["included_sections"] = include  # NEW (safe structured form)

        if exclude is not None:
            if not isinstance(exclude, list):
                raise ValueError("Invalid config: sections.exclude must be a list.")

            flattened["exclude"] = ",".join(str(s) for s in exclude)
            flattened["excluded_sections"] = exclude  # NEW (safe structured form)

    # -------------------------
    # Misc
    # -------------------------
    if "verbosity" in raw:
        flattened["verbosity"] = raw["verbosity"]

    return flattened