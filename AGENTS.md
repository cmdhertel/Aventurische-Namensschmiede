# Repository Guidelines

## Project Structure & Module Organization
Core Python code lives in `src/namegen/`. Use `cli.py` for the Typer entrypoint, `generator.py` for name generation, `loader.py` for TOML loading, and `models.py` for Pydantic models. Region data is stored in `src/namegen/data/*.toml`; each file represents one region and is auto-discovered by the loader. Tests live in `tests/` and generally mirror the module they cover, for example `tests/test_generator.py`. The web app is isolated in `web/` with `main.py`, `routes/`, `templates/`, and `static/`.

## Build, Test, and Development Commands
Use `uv` for local development.

- `uv sync` installs runtime and dev dependencies.
- `uv run pytest` runs the full test suite.
- `uv run pytest tests/test_generator.py::test_simple` runs one focused test.
- `uv run pytest --cov=namegen` checks coverage for core package changes.
- `uv run namegen regions` lists available regions from packaged data.
- `docker compose up --build` starts the web app locally on `http://localhost:8000`.

## Coding Style & Naming Conventions
Target Python 3.11+ and keep imports, type hints, and docstrings consistent with the existing codebase. Follow the current style: 4-space indentation, snake_case for functions/modules, PascalCase for Pydantic models and enums, and small focused functions. Keep region IDs lowercase with underscores, such as `mittelreich_kosch.toml`. Preserve the existing separation between package code in `src/namegen/` and web-specific code in `web/`.

## Testing Guidelines
Write `pytest` tests alongside the affected behavior and name them `test_<feature>.py` or `test_<behavior>()`. Prefer deterministic tests by passing a seeded `random.Random(...)` into generation code instead of patching global randomness. For data changes, add or update tests that verify loading and generated output shape. Run `uv run pytest` before opening a PR; use coverage when touching generation, loading, or output paths.

## Commit & Pull Request Guidelines
Recent history favors short, imperative commit subjects with an optional prefix, for example `docs: add explicit AI-assisted development disclaimer`. Keep commits scoped to one concern. PRs should explain the user-visible change, note test coverage, and link related issues when relevant. Include screenshots for template or styling updates and mention any new region data files explicitly.
