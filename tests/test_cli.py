"""Tests für die Typer-CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from namegen.cli import app

runner = CliRunner()


def test_professions_command_lists_all_user_facing_groups() -> None:
    result = runner.invoke(app, ["professions"])
    assert result.exit_code == 0
    for title in ("Geweihte", "Zauberer", "Kämpfer & Ordensleute", "Profane"):
        assert title in result.stdout


def test_simple_character_accepts_profession_category_alias() -> None:
    result = runner.invoke(
        app,
        [
            "simple",
            "mittelreich_kosch",
            "--character",
            "--profession-category",
            "geweihte",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    assert '"profession"' in result.stdout


def test_simple_experience_requires_character() -> None:
    result = runner.invoke(app, ["simple", "mittelreich_kosch", "--experience", "meister"])
    assert result.exit_code == 1
    assert "--experience erfordert --character" in result.stdout


def test_simple_profession_category_requires_character() -> None:
    result = runner.invoke(
        app,
        ["simple", "mittelreich_kosch", "--profession-category", "geweihte"],
    )
    assert result.exit_code == 1
    assert "--profession-category erfordert --character" in result.stdout


def test_compose_accepts_infix_probability_for_character_generation() -> None:
    result = runner.invoke(
        app,
        [
            "compose",
            "mittelreich_kosch",
            "--character",
            "--infix-probability",
            "0.5",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    assert '"experience"' in result.stdout


def test_compose_rejects_invalid_infix_probability() -> None:
    result = runner.invoke(
        app,
        ["compose", "mittelreich_kosch", "--infix-probability", "1.5"],
    )
    assert result.exit_code != 0


def test_simple_accepts_species_aggregate_id() -> None:
    result = runner.invoke(app, ["simple", "human", "--format", "json"])
    assert result.exit_code == 0
    assert '"species": "Mensch"' in result.stdout


def test_compose_rejects_selection_without_syllable_data() -> None:
    result = runner.invoke(app, ["compose", "thorwal"])
    assert result.exit_code == 1
    assert "Silbenbausteine" in result.stdout
