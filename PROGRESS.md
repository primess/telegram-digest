# tg-digest Progress

All implementation work must be resumable from this file plus `DIGEST.md`.

## Stage 0 — Scaffold + tooling

- [x] S0-T1 — Create repository skeleton. Acceptance: repo has `pyproject.toml`, `src/`, `tests/`, docs state files. Status: done. Notes: created locally at `/root/tg-digest`.
- [x] S0-T2 — Verify tooling. Acceptance: `pytest`, `ruff check .`, and `mypy src` run successfully. Status: done. Notes: `.venv` created; `pytest -q`, `ruff check .`, and `mypy src` pass with CLI smoke test.

## Stage 1 — Config + storage

- [ ] S1-T1 — Config models and YAML loaders. Acceptance: tests prove defaults, source validation, duplicate refusal, topic_id requirement, private/1:1 refusal. Status: todo. Notes: not started.
- [ ] S1-T2 — SQLite schema/bootstrap. Acceptance: tests prove required tables exist and runtime directories/permissions are created. Status: todo. Notes: not started.

## Stage 2 — Testbed

- [ ] S2-T1 — Protocols and fakes. Acceptance: FakeReader/FakeLLM/FakeBot/ClockFake/BudgetSimulator import and support placeholder E2E. Status: todo.
- [ ] S2-T2 — Placeholder fake E2E. Acceptance: `pytest -m e2e` produces digest-shaped object without network. Status: todo.

## Live endpoint gates

- [ ] User authorised Stage 12 real-Telegram smoke.
- [ ] User authorised Stage 13 real-bot smoke.
- [ ] User authorised Stage 14 Hermes integration.


### Stage 0 gate summary — 2026-04-24T13:06Z

- Commands run: `pytest -q`, `ruff check .`, `mypy src`.
- Result: all green.
- Spec proof: `tests/unit/test_cli.py::test_version_command_prints_package_version` proves package entrypoint wiring.
