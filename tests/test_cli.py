from __future__ import annotations

from typer.testing import CliRunner

from analyzer.cli import app

runner = CliRunner()


def test_help_runs_successfully():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "estimate-cost" in result.stdout
    assert "init-db" in result.stdout


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip()  # a non-empty version string


def test_estimate_cost_within_default_budget():
    result = runner.invoke(app, ["estimate-cost"])
    assert result.exit_code == 0
    assert "Estimated cost: $" in result.stdout
    assert "Within the default $8.00 project budget" in result.stdout


def test_estimate_cost_warns_when_over_budget():
    result = runner.invoke(
        app,
        [
            "estimate-cost",
            "--ranked-keywords-rows",
            "50000",
            "--domains",
            "6",
            "--serp-queries",
            "100",
        ],
    )
    assert result.exit_code == 0
    assert "WARNING: exceeds the default $8.00 project budget" in result.stdout
