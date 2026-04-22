# Copilot / AI agent instructions for Fairweather

Purpose
- Help AI coding agents be productive quickly in this repository (Halibut Bot).

Big picture
- This project computes fishing windows primarily from NOAA tide predictions. Core logic lives in `src/fairweather/tides.py` and exposes Pydantic models and helpers (`TideRequest`, `TidePrediction`, `fetch_tides`, `find_last_tide`, `find_next_tides`). The CLI entrypoint is `src/fairweather/main.py`.

Key files and where to look
- `src/fairweather/tides.py`: canonical place for API integration, pydantic models, timezone handling, and HTTP calls to NOAA.
- `src/fairweather/main.py`: example runner; note it currently imports `src.fairweather.tides` (see "quirks").
- `tests/test_tide_api.py`: shows testing patterns (monkeypatching `tides.datetime` and `tides.httpx.Client`) and expected behaviors for parsing and timezone-awareness.
- `pyproject.toml`: project metadata, runtime (Python >=3.14), and dependencies (`httpx`, `pydantic v2`, `pytest`).

Developer workflows (concrete commands)
- Run tests: `pytest -q` (activate your virtualenv; project uses a `src/` layout).
- Lint/format: project lists `ruff` and `pre-commit` in deps; run `pre-commit run --all-files` if configured.
- Run the app locally (recommended): set `PYTHONPATH=src` and run the module or pytest-targeted scripts. Example: `PYTHONPATH=src pytest` or `PYTHONPATH=src python -m fairweather.main`.

Project-specific conventions & patterns
- Source layout: `src/fairweather` is the package root. Most imports in tests and production code expect to import `fairweather.*` when `PYTHONPATH=src` or after installation.
- Pydantic v2 usage: models use `model_dump()`, `model_validate_json()`, `Field` aliases, `field_validator`, and `ConfigDict`. Follow existing patterns when adding fields/validators.
- Time handling: all parsing produces timezone-aware UTC datetimes (`timestamp` field). Conversions to local time are done via `local_time()` on `TidePrediction`.
- HTTP client pattern: `fetch_tides` uses `httpx.Client(http2=True)` within a `with` block and calls `response.raise_for_status()` before model validation.
- Tests monkeypatch `tides.datetime` and `tides.httpx.Client` rather than patching modules elsewhere — follow this pattern when writing tests.

Notable quirks and pitfalls
- `src/fairweather/main.py` currently imports `from src.fairweather.tides import ...` while the rest of the codebase (and tests) import `fairweather.*`. This inconsistent import style can break local runs; prefer `from fairweather.tides import ...` when editing code.
- Type hints vs runtime: `find_last_tide` is annotated to return `TidePrediction` but may return `None` when no past tides exist. Preserve existing behavior unless changing call sites.

Examples (use these as templates)
- HTTP mocking in tests: see `tests/test_tide_api.py` for `FakeClient` and monkeypatching `tides.httpx.Client`.
- Fixed-time tests: tests replace `tides.datetime` with a lightweight `FixedDT` that provides `now()` and preserves `fromisoformat()`.

When in doubt
- Read `src/fairweather/tides.py` first for expected data shapes and error handling.
- Mirror the testing approach in `tests/test_tide_api.py` when adding unit tests for time- or network-dependent logic.

If anything here is unclear or you want the agent to follow stricter rules (e.g., prefer absolute imports, change type hints, or auto-run tests on patch), tell me which conventions to enforce.
