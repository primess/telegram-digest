# tg-digest Progress

All implementation work must be resumable from this file plus `DIGEST.md`.

## Stage 0 — Scaffold + tooling

- [x] S0-T1 — Create repository skeleton. Acceptance: repo has `pyproject.toml`, `src/`, `tests/`, docs state files. Status: done. Notes: created locally at `/root/tg-digest`.
- [x] S0-T2 — Verify tooling. Acceptance: `pytest`, `ruff check .`, and `mypy src` run successfully. Status: done. Notes: `.venv` created; `pytest -q`, `ruff check .`, and `mypy src` pass with CLI smoke test.

## Stage 1 — Config + storage

- [x] S1-T1 — Config models and YAML loaders. Acceptance: tests prove defaults, source validation, duplicate refusal, topic_id requirement, private/1:1 refusal. Status: done. Notes: `tests/unit/test_sources_config.py`; implemented `tg_digest.config.sources`.
- [x] S1-T2 — SQLite schema/bootstrap. Acceptance: tests prove required tables exist and runtime directories/permissions are created. Status: done. Notes: `tests/unit/test_storage_bootstrap.py`; implemented `tg_digest.storage.bootstrap`.

## Stage 2 — Testbed

- [x] S2-T1 — Protocols and fakes. Acceptance: FakeReader/FakeLLM/FakeBot/ClockFake/BudgetSimulator import and support placeholder E2E. Status: done. Notes: implemented `tg_digest.types` and `tg_digest.testbed.fakes`.
- [x] S2-T2 — Placeholder fake E2E. Acceptance: `pytest -m e2e` produces digest-shaped object without network. Status: done. Notes: implemented `tg_digest.pipeline.fake_pipeline`; artifact written by FakeBot.

## Stage 3 — Filter + cluster

- [x] S3-T1 — Deterministic pre-filter. Acceptance: tests prove near-empty, pure empty media text, language mismatch, blacklist, and exact duplicate drops. Status: done. Notes: implemented `FilterCluster.filter`.
- [x] S3-T2 — Deterministic similarity clustering. Acceptance: tests prove similar messages are grouped, representative is longest, traction counts cluster size. Status: done. Notes: implemented shingled Jaccard clustering.

### Stage 3 gate summary — 2026-04-24T13:22Z

- Commands run: `pytest -q`, `ruff check .`, `mypy src`.
- Result: all green (15 tests).
- Spec proof: `tests/unit/test_filter_cluster.py` covers §8.2 pre-filter and §8.3 deterministic clustering first pass.

## Live endpoint gates

- [ ] User authorised Stage 12 real-Telegram smoke.
- [ ] User authorised Stage 13 real-bot smoke.
- [ ] User authorised Stage 14 Hermes integration.


### Stage 0 gate summary — 2026-04-24T13:06Z

- Commands run: `pytest -q`, `ruff check .`, `mypy src`.
- Result: all green.
- Spec proof: `tests/unit/test_cli.py::test_version_command_prints_package_version` proves package entrypoint wiring.


### Stage 1 gate summary — 2026-04-24T13:13Z

- Commands run: `pytest -q`, `ruff check .`, `mypy src`.
- Result: all green (8 tests).
- Spec proof: source config tests cover §6 allowlist validation safety; storage bootstrap tests cover §12 runtime layout/tables.


### Stage 2 gate summary — 2026-04-24T13:18Z

- Commands run: `pytest -q`, `pytest -m e2e -q`, `ruff check .`, `mypy src`.
- Result: all green (13 tests; fake E2E green).
- Spec proof: fakes from §22.3 exist in first pass and E2E proves a no-network digest-shaped object can be produced before any live endpoint.
