"""Tests for the ``mounts`` CLI in ``src/scripts/cli.py``."""

import os
import sys

from scripts import cli as cli_module
from scripts.cli import cli

import pandas as pd
from click.testing import CliRunner


def test_save_writes_csv(tmp_path, monkeypatch, fake_df):
    """``mounts save --type csv --output-dir X`` writes the merged file under X."""
    def fake_extract(self, volcanoes=None):
        self.data = {"slamet-263180": fake_df}
        self.catalogs = [{"name": "Slamet", "code": "263180", "updated_at": None}]
        return self

    monkeypatch.setattr(
        cli_module.MountsProject, "extract", fake_extract, raising=True
    )

    runner = CliRunner()
    result = runner.invoke(
        cli, ["save", "--type", "csv", "--output-dir", str(tmp_path)]
    )

    assert result.exit_code == 0, result.output
    merged = tmp_path / "all-volcanoes.csv"
    assert merged.exists(), f"expected {merged} to be written"
    df = pd.read_csv(merged)
    assert {"value", "type"}.issubset(df.columns)


def test_dashboard_invokes_streamlit(monkeypatch):
    """``mounts dashboard`` shells out to ``python -m streamlit run <dashboard.py>``."""
    captured: dict = {}

    def fake_call(cmd, *args, **kwargs):
        captured["cmd"] = cmd
        return 0

    monkeypatch.setattr(cli_module.subprocess, "call", fake_call)

    runner = CliRunner()
    result = runner.invoke(cli, ["dashboard", "--server.port", "9000"])

    assert result.exit_code == 0, result.output
    cmd = captured["cmd"]
    assert cmd[0] == sys.executable
    assert cmd[1:4] == ["-m", "streamlit", "run"]
    assert os.path.basename(cmd[4]) == "dashboard.py"
    assert os.path.isabs(cmd[4])
    assert cmd[5:] == ["--server.port", "9000"]


def test_help_lists_subcommands():
    """``mounts --help`` advertises both subcommands."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "save" in result.output
    assert "dashboard" in result.output
