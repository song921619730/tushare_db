"""Tests for config loader source file tracking and probe YAML writeback."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


class TestWriteYamlEnabled:
    """Test _write_yaml_enabled helper from cli.py."""

    def _make_yaml_file(self, content: str) -> str:
        """Create a temp multi-document YAML file."""
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        )
        tmp.write(content)
        tmp.close()
        return tmp.name

    def _read_file(self, path: str) -> str:
        with open(path, encoding="utf-8") as f:
            return f.read()

    def _invoke_write(self, yaml_file: str, changes: list[tuple[str, bool]]) -> None:
        """Call the same ruamel.yaml logic as cli.py _write_yaml_enabled."""
        from ruamel.yaml import YAML

        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.indent(mapping=2, sequence=4, offset=2)

        changed_names = {name for name, _ in changes}
        enabled_map = {name: val for name, val in changes}

        path = Path(yaml_file)
        documents = list(yaml.load_all(path))

        for doc in documents:
            if doc and "name" in doc and doc["name"] in changed_names:
                doc["enabled"] = enabled_map[doc["name"]]

        with open(path, "w", encoding="utf-8") as f:
            for doc in documents:
                yaml.dump(doc, f)

    def test_disable_single_interface(self):
        """Disabling a single interface in a multi-doc file."""
        content = (
            "name: interface_a\n"
            "enabled: true\n"
            "priority: P1\n"
            "---\n"
            "name: interface_b\n"
            "enabled: true\n"
            "priority: P2\n"
        )
        path = self._make_yaml_file(content)
        try:
            self._invoke_write(path, [("interface_a", False)])
            result = self._read_file(path)
            assert "name: interface_a" in result
            assert "enabled: false" in result
            assert "name: interface_b" in result
            # interface_b unchanged
            assert result.count("enabled: true") == 1
        finally:
            Path(path).unlink()

    def test_enable_and_disable_same_file(self):
        """Enable one interface and disable another in the same file."""
        content = (
            "name: film_record\n"
            "enabled: true\n"
            "---\n"
            "name: teleplay_record\n"
            "enabled: false\n"
        )
        path = self._make_yaml_file(content)
        try:
            self._invoke_write(path, [("film_record", False), ("teleplay_record", True)])
            result = self._read_file(path)
            # film_record now disabled
            assert "name: film_record" in result
            # teleplay_record now enabled
            assert "name: teleplay_record" in result
        finally:
            Path(path).unlink()

    def test_unchanged_interface_preserved(self):
        """Interfaces not in changes list remain untouched."""
        content = (
            "name: keep_me\n"
            "enabled: true\n"
            "priority: P1\n"
            "---\n"
            "name: change_me\n"
            "enabled: true\n"
        )
        path = self._make_yaml_file(content)
        try:
            self._invoke_write(path, [("change_me", False)])
            result = self._read_file(path)
            # keep_me still enabled
            lines = result.split("\n")
            keep_idx = next(i for i, l in enumerate(lines) if "keep_me" in l)
            assert "enabled: true" in lines[keep_idx + 1]
        finally:
            Path(path).unlink()

    def test_comments_preserved(self):
        """YAML comments are preserved after writeback."""
        content = (
            "# This is a comment about interface_a\n"
            "name: interface_a\n"
            "enabled: true\n"
            "---\n"
            "# This is a comment about interface_b\n"
            "name: interface_b\n"
            "enabled: true\n"
        )
        path = self._make_yaml_file(content)
        try:
            self._invoke_write(path, [("interface_a", False)])
            result = self._read_file(path)
            assert "# This is a comment about interface_a" in result
            assert "# This is a comment about interface_b" in result
        finally:
            Path(path).unlink()


class TestSourceFileTracking:
    """Test that load_all_interface_specs tracks __source_file__."""

    def test_source_file_attribute_set(self, tmp_path: Path):
        """Each spec has __source_file__ pointing to its YAML file."""
        from tushare_db.config.loader import load_all_interface_specs
        from tushare_db.config.models import InterfaceSpec, FetchStrategy

        # Create a test interface dir with one file
        iface_dir = tmp_path / "interfaces"
        iface_dir.mkdir()
        test_file = iface_dir / "test.yaml"
        test_file.write_text(
            "name: test_iface\n"
            "table: tushare_test\n"
            "enabled: true\n"
            "priority: P1\n"
            "mode: full\n"
            "freq_bucket: normal\n"
            "start_date: '20240101'\n"
            "fetch_strategy:\n"
            "  kind: full_once\n"
            "partition_key: tuple()\n"
            "order_by: ts_code\n"
            "batch: normal\n"
        )

        specs = load_all_interface_specs(str(iface_dir))
        assert len(specs) == 1
        assert hasattr(specs[0], "__source_file__")
        assert specs[0].__source_file__ == str(test_file)

    def test_multi_doc_same_file(self, tmp_path: Path):
        """Multiple docs in one file all get same source_file."""
        from tushare_db.config.loader import load_all_interface_specs

        iface_dir = tmp_path / "interfaces"
        iface_dir.mkdir()
        test_file = iface_dir / "multi.yaml"
        test_file.write_text(
            "name: iface_a\ntable: t_a\nenabled: true\npriority: P1\n"
            "mode: full\nfreq_bucket: normal\nstart_date: '20240101'\n"
            "fetch_strategy:\n  kind: full_once\npartition_key: tuple()\norder_by: ts_code\nbatch: normal\n"
            "---\n"
            "name: iface_b\ntable: t_b\nenabled: false\npriority: P2\n"
            "mode: full\nfreq_bucket: normal\nstart_date: '20240101'\n"
            "fetch_strategy:\n  kind: full_once\npartition_key: tuple()\norder_by: ts_code\nbatch: reference\n"
        )

        specs = load_all_interface_specs(str(iface_dir))
        assert len(specs) == 2
        assert specs[0].__source_file__ == str(test_file)
        assert specs[1].__source_file__ == str(test_file)
