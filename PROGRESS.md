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

## Stage 4 — Scorer + selector

- [x] S4-T1 — Weighted scorer. Acceptance: tests prove source, topic, keyword, traction, and length components contribute to score and reason text. Status: done. Notes: implemented `tg_digest.scorer.core.Scorer.score`.
- [x] S4-T2 — Selector math. Acceptance: tests prove known percentage, floor, cap, and exploration slot selection. Status: done. Notes: implemented `Scorer.select`; optional LLM tie-breaker still deferred.

### Stage 4 gate summary — 2026-04-24T13:26Z

- Commands run: `pytest -q`, `ruff check .`, `mypy src`.
- Result: all green (17 tests).
- Spec proof: `tests/unit/test_scorer.py` covers §8.4 scoring and §8.5 selection first pass.

## Stage 5 — LLM accounting + budget enforcer

- [x] S5-T1 — Accounting wrapper. Acceptance: tests prove LLM calls record `(run_id, model, purpose, input_tokens, output_tokens, cost, ts)` to SQLite. Status: done. Notes: implemented `tg_digest.llm.accounting.AccountedLLM`.
- [x] S5-T2 — Per-run hard stop. Acceptance: tests prove budget is checked before LLM call, no usage is recorded after refused call, and checkpoint is exposed. Status: done. Notes: implemented `BudgetEnforcer`/`BudgetExceeded`; subscription-window calibration still future.

### Stage 5 gate summary — 2026-04-24T13:31Z

- Commands run: `pytest -q`, `ruff check .`, `mypy src`.
- Result: all green (19 tests).
- Spec proof: `tests/unit/test_llm_accounting.py` covers §11.1 accounting and §11.3 hard-stop-before-call checkpoint behavior first pass.

## Stage 6 — Summariser

- [x] S6-T1 — FakeLLM summariser. Acceptance: tests prove selected scored clusters become digest items with stable ids, summaries, links, source ids, and Telegram deeplinks. Status: done. Notes: implemented `tg_digest.summariser.core.Summariser`; real Anthropic/cassette path still future.

### Stage 6 gate summary — 2026-04-24T13:35Z

- Commands run: `pytest -q`, `pytest -m e2e -q`, `ruff check .`, `mypy src`.
- Result: all green (20 tests; fake E2E green).
- Spec proof: `tests/unit/test_summariser.py` covers §8.6 selected-item summarisation first pass.

## Stage 7 — Digest assembly + digest-index

- [x] S7-T1 — Digest assembler. Acceptance: tests prove assembled digest dict includes §8.7 top-level fields plus item kind/score/reason/source/link/deeplink/flags. Status: done. Notes: implemented `tg_digest.digest.assembly.DigestAssembler`.
- [x] S7-T2 — Digest-index persistence. Acceptance: tests prove digest items persist in SQLite and resolve by callback `item_id`. Status: done. Notes: implemented `DigestIndexStore`.

### Stage 7 gate summary — 2026-04-24

- Commands run: `pytest -q`, `ruff check .`, `mypy src`.
- Result: all green (22 tests).
- Spec proof: `tests/unit/test_digest_assembly.py` covers §8.7 digest object shape and §7/§10 callback item resolution support.

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
