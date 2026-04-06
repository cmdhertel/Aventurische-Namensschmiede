"""Tests für die Typer-CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from namegen.cli import app
from namegen.models import Gender, GenerationMode, NameResult

runner = CliRunner()


def test_professions_command_lists_all_user_facing_groups() -> None:
    result = runner.invoke(app, ["professions"])
    assert result.exit_code == 0
    for title in ("Geweihte", "Zauberer", "Kämpfer & Ordensleute", "Profane"):
        assert title in result.stdout
    assert "graumagier_aus_perricum" in result.stdout


def test_professions_command_for_selection_shows_only_selection_preview() -> None:
    result = runner.invoke(app, ["professions", "mittelreich_perricum"])

    assert result.exit_code == 0
    assert "Graumagier aus Perricum" in result.stdout
    assert "graumagier_aus_perricum" in result.stdout
    assert "Koschbauer" not in result.stdout


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


def test_simple_profession_theme_requires_character() -> None:
    result = runner.invoke(
        app,
        ["simple", "mittelreich_perricum", "--profession-theme", "graumagier_aus_perricum"],
    )
    assert result.exit_code == 1
    assert "--profession-theme erfordert --character" in result.stdout


def test_simple_character_accepts_profession_theme() -> None:
    result = runner.invoke(
        app,
        [
            "simple",
            "mittelreich_perricum",
            "--character",
            "--profession-category",
            "zauberer",
            "--profession-theme",
            "graumagier_aus_perricum",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    assert "Graumagier aus Perricum" in result.stdout


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


def test_compose_accepts_syllable_limits() -> None:
    result = runner.invoke(
        app,
        [
            "compose",
            "mittelreich_kosch",
            "--min-syllables",
            "2",
            "--max-syllables",
            "2",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    assert '"components"' in result.stdout


def test_simple_exclude_file_omits_used_name(tmp_path: Path) -> None:
    used = tmp_path / "used_names.txt"
    used.write_text("Yppolita di Marcia\n", encoding="utf-8")

    captured = {}

    def fake_generate(*, region, mode=GenerationMode.SIMPLE, gender=Gender.ANY, **kwargs):
        captured["exclude_names"] = kwargs.get("exclude_names")
        return NameResult.build(
            first="Test",
            last="Name",
            gender=gender,
            region=region,
            mode=mode,
        )

    import namegen.cli as cli_module

    original_generate = cli_module.generate
    cli_module.generate = fake_generate
    try:
        result = runner.invoke(
            app,
            [
                "simple",
                "horasreich",
                "--exclude-file",
                str(used),
                "--format",
                "plain",
            ],
        )
    finally:
        cli_module.generate = original_generate

    assert result.exit_code == 0
    assert captured["exclude_names"] == {"yppolita di marcia"}


def test_config_profile_save_and_load(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    save_result = runner.invoke(
        app,
        [
            "config",
            "save",
            "testprofil",
            "--region",
            "mittelreich_kosch",
            "--mode",
            "compose",
            "--gender",
            "female",
            "--count",
            "3",
            "--format",
            "json",
            "--profession-theme",
            "graumagier_aus_perricum",
            "--min-syllables",
            "2",
            "--max-syllables",
            "2",
        ],
    )
    assert save_result.exit_code == 0

    load_result = runner.invoke(app, ["config", "load", "testprofil"])
    assert load_result.exit_code == 0
    assert '"region": "mittelreich_kosch"' in load_result.stdout
    assert '"mode": "compose"' in load_result.stdout
    assert '"profession_theme": "graumagier_aus_perricum"' in load_result.stdout


def test_compose_can_use_profile_defaults(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    save_result = runner.invoke(
        app,
        [
            "config",
            "save",
            "kurz",
            "--region",
            "mittelreich_kosch",
            "--mode",
            "compose",
            "--gender",
            "male",
            "--count",
            "1",
            "--format",
            "json",
            "--min-syllables",
            "2",
            "--max-syllables",
            "2",
        ],
    )
    assert save_result.exit_code == 0

    run_result = runner.invoke(app, ["compose", "--profile", "kurz"])
    assert run_result.exit_code == 0
    assert '"mode": "compose"' in run_result.stdout
