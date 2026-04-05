"""Tests für die Ausgabe-Formate (output.py)."""

from __future__ import annotations

import csv
import io
import json
import random

import pytest

from namegen.chargen import generate_character
from namegen.generator import generate
from namegen.models import (
    CharacterResult,
    GenerationMode,
    NameResult,
)
from namegen.output import (
    OutputFormat,
    _chars_to_csv,
    _chars_to_json,
    _chars_to_plain,
    _format_components,
    _to_csv,
    _to_json,
    _to_markdown,
    _to_plain,
    default_filename,
    write,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _name_results(n: int = 3, region: str = "mittelreich_kosch") -> list[NameResult]:
    return [generate(region, rng=random.Random(i)) for i in range(n)]


def _compose_results(n: int = 3) -> list[NameResult]:
    return [
        generate("mittelreich_kosch", mode=GenerationMode.COMPOSE, rng=random.Random(i))
        for i in range(n)
    ]


def _char_results(n: int = 2) -> list[CharacterResult]:
    return [generate_character("mittelreich_kosch", rng=random.Random(i)) for i in range(n)]


# ── write(): leere Liste ──────────────────────────────────────────────────────


def test_write_empty_returns_silently(capsys: pytest.CaptureFixture) -> None:
    write([], fmt=OutputFormat.PLAIN)
    captured = capsys.readouterr()
    assert captured.out == ""


# ── _to_plain ─────────────────────────────────────────────────────────────────


def test_to_plain_contains_all_names() -> None:
    results = _name_results()
    text = _to_plain(results)
    for r in results:
        assert r.full_name in text


def test_to_plain_ends_with_newline() -> None:
    text = _to_plain(_name_results(1))
    assert text.endswith("\n")


def test_to_plain_one_name_per_line() -> None:
    results = _name_results(3)
    lines = _to_plain(results).strip().splitlines()
    assert len(lines) == 3
    for i, line in enumerate(lines):
        assert results[i].full_name == line


# ── _to_json ──────────────────────────────────────────────────────────────────


def test_to_json_valid_json() -> None:
    text = _to_json(_name_results(3))
    data = json.loads(text)
    assert isinstance(data, list)
    assert len(data) == 3


def test_to_json_contains_required_keys() -> None:
    data = json.loads(_to_json(_name_results(1)))
    record = data[0]
    for key in ("full_name", "first_name", "gender", "region", "mode", "species", "culture"):
        assert key in record, f"Schlüssel '{key}' fehlt im JSON"


def test_to_json_full_name_matches() -> None:
    results = _name_results(2)
    data = json.loads(_to_json(results))
    for i, record in enumerate(data):
        assert record["full_name"] == results[i].full_name


def test_to_json_no_none_values() -> None:
    """exclude_none=True: kein Wert darf null sein."""
    data = json.loads(_to_json(_name_results(5)))
    for record in data:
        for value in record.values():
            assert value is not None


def test_to_json_ends_with_newline() -> None:
    assert _to_json(_name_results(1)).endswith("\n")


# ── _to_csv ───────────────────────────────────────────────────────────────────


def _parse_csv(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


def test_to_csv_header_columns() -> None:
    text = _to_csv(_name_results(1), show_components=False)
    reader = csv.reader(io.StringIO(text))
    header = next(reader)
    for col in (
        "full_name",
        "first_name",
        "last_name",
        "gender",
        "species",
        "culture",
        "region",
        "mode",
    ):
        assert col in header


def test_to_csv_row_count_matches() -> None:
    results = _name_results(4)
    rows = _parse_csv(_to_csv(results, show_components=False))
    assert len(rows) == 4


def test_to_csv_names_match() -> None:
    results = _name_results(3)
    rows = _parse_csv(_to_csv(results, show_components=False))
    for i, row in enumerate(rows):
        assert row["full_name"] == results[i].full_name


def test_to_csv_gender_values_valid() -> None:
    rows = _parse_csv(_to_csv(_name_results(10), show_components=False))
    valid = {"male", "female", "any"}
    for row in rows:
        assert row["gender"] in valid


def test_to_csv_compose_columns_present() -> None:
    results = _compose_results(2)
    text = _to_csv(results, show_components=True)
    header_line = text.splitlines()[0]
    for col in ("first_prefix", "first_suffix"):
        assert col in header_line


def test_to_csv_compose_prefix_suffix_nonempty() -> None:
    results = _compose_results(3)
    rows = _parse_csv(_to_csv(results, show_components=True))
    for row in rows:
        assert row["first_prefix"] != "" or row["first_suffix"] != ""


# ── _to_markdown ──────────────────────────────────────────────────────────────


def test_to_markdown_has_table_separator() -> None:
    text = _to_markdown(_name_results(2), show_components=False)
    assert "---" in text


def test_to_markdown_contains_all_names() -> None:
    results = _name_results(3)
    text = _to_markdown(results, show_components=False)
    for r in results:
        assert r.full_name in text


def test_to_markdown_has_region_header() -> None:
    results = _name_results(1)
    text = _to_markdown(results, show_components=False)
    assert results[0].region in text


def test_to_markdown_pipe_delimited_rows() -> None:
    text = _to_markdown(_name_results(2), show_components=False)
    data_lines = [line for line in text.splitlines() if line.startswith("|") and "---" not in line]
    # header + 2 data rows
    assert len(data_lines) >= 3


def test_to_markdown_compose_has_bausteine_column() -> None:
    results = _compose_results(2)
    text = _to_markdown(results, show_components=True)
    assert "Bausteine" in text


# ── write() → stdout (PLAIN / JSON / CSV / MARKDOWN) ─────────────────────────


def test_write_plain_to_stdout(capsys: pytest.CaptureFixture) -> None:
    results = _name_results(2)
    write(results, fmt=OutputFormat.PLAIN)
    captured = capsys.readouterr()
    for r in results:
        assert r.full_name in captured.out


def test_write_json_to_stdout(capsys: pytest.CaptureFixture) -> None:
    write(_name_results(2), fmt=OutputFormat.JSON)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 2


def test_write_csv_to_stdout(capsys: pytest.CaptureFixture) -> None:
    results = _name_results(2)
    write(results, fmt=OutputFormat.CSV)
    captured = capsys.readouterr()
    rows = _parse_csv(captured.out)
    assert len(rows) == 2


def test_write_markdown_to_stdout(capsys: pytest.CaptureFixture) -> None:
    results = _name_results(2)
    write(results, fmt=OutputFormat.MARKDOWN)
    captured = capsys.readouterr()
    assert "---" in captured.out
    for r in results:
        assert r.full_name in captured.out


# ── write() → Datei ───────────────────────────────────────────────────────────


def test_write_plain_to_file(tmp_path) -> None:
    results = _name_results(3)
    out = tmp_path / "names.txt"
    write(results, fmt=OutputFormat.PLAIN, dest=out)
    content = out.read_text(encoding="utf-8")
    for r in results:
        assert r.full_name in content


def test_write_json_to_file(tmp_path) -> None:
    results = _name_results(3)
    out = tmp_path / "names.json"
    write(results, fmt=OutputFormat.JSON, dest=out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) == 3


def test_write_csv_to_file(tmp_path) -> None:
    results = _name_results(3)
    out = tmp_path / "names.csv"
    write(results, fmt=OutputFormat.CSV, dest=out)
    rows = _parse_csv(out.read_text(encoding="utf-8"))
    assert len(rows) == 3


# ── Charakter: _chars_to_plain ────────────────────────────────────────────────


def test_chars_to_plain_contains_names() -> None:
    results = _char_results(2)
    text = _chars_to_plain(results)
    for r in results:
        assert r.full_name in text


def test_chars_to_plain_contains_traits() -> None:
    results = _char_results(1)
    text = _chars_to_plain(results)
    t = results[0].traits
    assert t.physical.hair in text
    assert t.personality in text
    assert t.quirk in text


def test_chars_to_plain_contains_profession_and_age() -> None:
    results = _char_results(1)
    text = _chars_to_plain(results)
    assert results[0].profession in text
    assert str(results[0].age) in text


# ── Charakter: _chars_to_json ─────────────────────────────────────────────────


def test_chars_to_json_valid_json() -> None:
    data = json.loads(_chars_to_json(_char_results(2)))
    assert isinstance(data, list)
    assert len(data) == 2


def test_chars_to_json_has_required_top_level_keys() -> None:
    record = json.loads(_chars_to_json(_char_results(1)))[0]
    for key in ("name", "age", "profession", "traits", "species", "culture", "language"):
        assert key in record


def test_chars_to_json_traits_has_all_fields() -> None:
    traits = json.loads(_chars_to_json(_char_results(1)))[0]["traits"]
    for key in ("hair", "eyes", "build", "personality", "motivation", "quirk"):
        assert key in traits, f"Traits-Schlüssel '{key}' fehlt"


def test_chars_to_json_age_is_integer() -> None:
    record = json.loads(_chars_to_json(_char_results(1)))[0]
    assert isinstance(record["age"], int)


def test_chars_to_json_name_block_has_full_name() -> None:
    record = json.loads(_chars_to_json(_char_results(1)))[0]
    assert "full_name" in record["name"]


# ── Charakter: _chars_to_csv ──────────────────────────────────────────────────


def test_chars_to_csv_header_columns() -> None:
    text = _chars_to_csv(_char_results(1))
    header = next(csv.reader(io.StringIO(text)))
    for col in (
        "full_name",
        "gender",
        "species",
        "culture",
        "region",
        "age",
        "profession",
        "language",
        "script",
        "social_status",
        "hair",
        "eyes",
        "build",
        "personality",
        "motivation",
        "quirk",
    ):
        assert col in header


def test_chars_to_csv_row_count() -> None:
    results = _char_results(3)
    rows = _parse_csv(_chars_to_csv(results))
    assert len(rows) == 3


def test_chars_to_csv_age_is_numeric() -> None:
    rows = _parse_csv(_chars_to_csv(_char_results(3)))
    for row in rows:
        assert row["age"].isdigit()


def test_chars_to_csv_names_match() -> None:
    results = _char_results(2)
    rows = _parse_csv(_chars_to_csv(results))
    for i, row in enumerate(rows):
        assert row["full_name"] == results[i].full_name


# ── write() mit CharacterResult ───────────────────────────────────────────────


def test_write_characters_plain_to_stdout(capsys: pytest.CaptureFixture) -> None:
    results = _char_results(1)
    write(results, fmt=OutputFormat.PLAIN)
    captured = capsys.readouterr()
    assert results[0].full_name in captured.out


def test_write_characters_json_to_stdout(capsys: pytest.CaptureFixture) -> None:
    results = _char_results(1)
    write(results, fmt=OutputFormat.JSON)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 1
    assert "traits" in data[0]


def test_write_characters_csv_to_file(tmp_path) -> None:
    results = _char_results(2)
    out = tmp_path / "chars.csv"
    write(results, fmt=OutputFormat.CSV, dest=out)
    rows = _parse_csv(out.read_text(encoding="utf-8"))
    assert len(rows) == 2
    assert "profession" in rows[0]


# ── write() Dispatcher: CharacterResult vs NameResult ────────────────────────


def test_write_dispatcher_detects_character_result(capsys: pytest.CaptureFixture) -> None:
    """write() muss CharacterResult automatisch erkennen und traits ausgeben."""
    results = _char_results(1)
    write(results, fmt=OutputFormat.PLAIN)
    captured = capsys.readouterr()
    # Nur der Character-Pfad gibt Traits aus
    assert results[0].traits.physical.hair in captured.out


def test_write_dispatcher_detects_name_result(capsys: pytest.CaptureFixture) -> None:
    """write() darf bei NameResult keine Charakter-Felder ausgeben."""
    results = _name_results(1)
    write(results, fmt=OutputFormat.PLAIN)
    captured = capsys.readouterr()
    assert "Äußeres" not in captured.out
    assert "Eigenart" not in captured.out


# ── _format_components ────────────────────────────────────────────────────────


def test_format_components_no_infix() -> None:
    r = generate("mittelreich_kosch", mode=GenerationMode.COMPOSE, rng=random.Random(0))
    if r.components and r.components.first_infix is None:
        text = _format_components(r)
        assert "+" in text or text  # mindestens prefix+suffix vorhanden


def test_format_components_reconstructs_first_name() -> None:
    for i in range(10):
        r = generate("mittelreich_kosch", mode=GenerationMode.COMPOSE, rng=random.Random(i))
        if r.components:
            text = _format_components(r)
            c = r.components
            parts = [p for p in [c.first_prefix, c.first_infix, c.first_suffix] if p]
            for part in parts:
                assert part in text


def test_format_components_returns_empty_for_none() -> None:
    r = generate("mittelreich_kosch", mode=GenerationMode.SIMPLE, rng=random.Random(0))
    assert _format_components(r) == ""


# ── default_filename ──────────────────────────────────────────────────────────


def test_default_filename_txt() -> None:
    name = default_filename(OutputFormat.PLAIN, "Kosch")
    assert name.endswith(".txt")
    assert "kosch" in name


def test_default_filename_json() -> None:
    name = default_filename(OutputFormat.JSON, "Horasreich")
    assert name.endswith(".json")
    assert "horasreich" in name


def test_default_filename_csv() -> None:
    assert default_filename(OutputFormat.CSV, "Bornland").endswith(".csv")


def test_default_filename_markdown() -> None:
    assert default_filename(OutputFormat.MARKDOWN, "Aranien").endswith(".md")


def test_default_filename_pdf() -> None:
    assert default_filename(OutputFormat.PDF, "Kosch").endswith(".pdf")


def test_default_filename_spaces_replaced() -> None:
    name = default_filename(OutputFormat.PLAIN, "Al'Anfa")
    assert " " not in name


def test_default_filename_is_lowercase() -> None:
    name = default_filename(OutputFormat.JSON, "Mittelreich")
    # slug portion should be lowercase
    assert name == name.lower()
