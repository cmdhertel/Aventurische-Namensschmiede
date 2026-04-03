# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync                        # install deps + dev deps
uv run namegen regions         # list available regions
uv run namegen simple kosch --gender female --count 5
uv run namegen compose mittelreich --gender male --count 3 --components
uv run pytest                  # run all tests
uv run pytest tests/test_generator.py::test_simple  # single test
```

## Architecture

**Source layout:** `src/namegen/` (src layout, hatchling build backend).

**Data layer:** Region data lives in `src/namegen/data/*.toml`. Each file is one DSA region. `loader.py` accesses them via `importlib.resources.files("namegen.data")` — this is zip-safe and works in editable + installed mode. Results are `lru_cache`d per process. The `data/__init__.py` is required for `importlib.resources` to treat the directory as a package.

**Data schema** (`[meta]`, `[simple]`, `[compose]` sections):
- `[simple.first]` / `[simple.last]`: plain name lists split into `male`, `female`, `neutral` keys. The generator merges gender-specific + neutral lists into one pool (neutral is always included, not a pure fallback).
- `[compose.first]` / `[compose.last]`: syllable building blocks with `infix_probability` (float 0–1) and per-gender sub-tables (`male`, `female`, `neutral`), each having `prefix`, `infix`, `suffix` lists. Pattern: `prefix + [infix] + suffix`.

**Generation flow:** `cli.py` → `generate()` in `generator.py` → `load_region()` in `loader.py` → `RegionData` (Pydantic model in `models.py`).

**Adding a new region:** Drop a new `<region_id>.toml` file into `src/namegen/data/`. No code changes needed. The region is immediately available via `namegen regions` and all commands. Use an existing TOML as template.

**`NameResult`** is the structured return type from `generate()`. It always carries `first_name`, `last_name` (nullable), `full_name`, `gender`, `region`, `mode`, and optionally `components` (syllable breakdown, compose mode only).

**Testing with deterministic output:** Pass a seeded `random.Random(seed)` as the `rng` parameter to `generate()` to avoid monkeypatching the global module.
