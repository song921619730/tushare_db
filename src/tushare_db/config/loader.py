"""Load and parse interface specifications from config/interfaces/*.yaml."""

from __future__ import annotations

import os
import re
from pathlib import Path

import yaml

from tushare_db.config.models import InterfaceSpec, FetchStrategy

ENV_VAR_RE = re.compile(r"\$\{([^}]+)\}")


def _resolve_env(value: str) -> str:
    """Resolve ${VAR} patterns from environment variables."""
    def replacer(m: re.Match) -> str:
        expr = m.group(1)
        if ":-" in expr:
            var, default = expr.split(":-", 1)
            return os.environ.get(var, default)
        return os.environ.get(expr, expr)
    return ENV_VAR_RE.sub(replacer, value)


def load_interface_specs(interface_dir: str = "config/interfaces") -> list[InterfaceSpec]:
    """Load all enabled interface specs from YAML files.

    Returns list of InterfaceSpec objects, skipping disabled (paid) entries.
    """
    specs: list[InterfaceSpec] = []
    dir_path = Path(interface_dir)

    if not dir_path.exists():
        raise FileNotFoundError(f"Interface directory not found: {interface_dir}")

    for yaml_file in sorted(dir_path.glob("*.yaml")):
        if yaml_file.name.startswith("_"):
            continue

        with open(yaml_file, encoding="utf-8") as f:
            for doc in yaml.safe_load_all(f):
                if doc is None:
                    continue
                spec = InterfaceSpec.model_validate(doc)
                specs.append(spec)

    return specs


def load_all_interface_specs(
    interface_dir: str = "config/interfaces",
) -> list[InterfaceSpec]:
    """Load all interface specs including disabled (paid) ones."""
    specs: list[InterfaceSpec] = []
    dir_path = Path(interface_dir)

    if not dir_path.exists():
        raise FileNotFoundError(f"Interface directory not found: {interface_dir}")

    for yaml_file in sorted(dir_path.glob("*.yaml")):
        if yaml_file.name.startswith("_"):
            continue

        with open(yaml_file, encoding="utf-8") as f:
            for doc in yaml.safe_load_all(f):
                if doc is None:
                    continue
                spec = InterfaceSpec.model_validate(doc)
                spec.__source_file__ = str(yaml_file)  # type: ignore[attr-defined]
                specs.append(spec)

    return specs


def load_settings(settings_path: str = "config/settings.yaml") -> dict:
    """Load global settings with environment variable resolution."""
    path = Path(settings_path)
    if not path.exists():
        return {}

    with open(path, encoding="utf-8") as f:
        content = f.read()

    content = _resolve_env(content)
    return yaml.safe_load(content) or {}
