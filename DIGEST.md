# tg-digest State Digest

## Completion estimate

- Stage-count estimate: 9 of 16 stages (0–8) are implemented/gated locally: about 56%.
- V1 deliverable checklist estimate: about 45% complete. Core deterministic pipeline + fakes exist; real Telegram/bot, feedback commands, preferences/review, CLI/dryrun, docs/handover are still pending.
- Codex quota policy: user asked to pause at 92% weekly and continue this session only until about 90%. Last user-provided reference was 84% weekly; no live quota meter is available inside tools.

## Built

- Repository scaffold exists at `/root/tg-digest`.
- Python package skeleton under `src/tg_digest`.
- Typer CLI entrypoint with `tg-digest version`.
- Config module: `tg_digest.config.sources` loads `sources.yaml`, applies defaults, refuses bad slugs, duplicate handles/ids, unsupported private/1:1 kinds, and `topic` without `topic_id`.
- Storage module: `tg_digest.storage.bootstrap` creates runtime dirs and initializes SQLite tables from §12 plus `llm_usage(purpose)`.
- Testbed first pass: `FakeReader`, `FakeLLM`, `FakeBot`, `ClockFake`, `BudgetSimulator`.
- Shared dataclasses in `tg_digest.types`.
- Placeholder no-network fake pipeline in `tg_digest.pipeline.fake_pipeline`.
- Filter/cluster module: deterministic text normalization, URL/emoji stripping, language heuristic, blacklist/exact-dedup filtering, shingled Jaccard clustering, representative selection, traction count.
- Scorer/selector module: weighted deterministic score, selection reason strings, percentage/floor/cap selection, exploration slot picking by novelty/traction.
- LLM accounting/budget first pass: `AccountedLLM`, `BudgetEnforcer`, `BudgetExceeded`, SQLite usage recording, pre-call hard-stop with checkpoint.
- Summariser first pass: converts selected `ScoredCluster`s into stable `DigestItem`s via FakeLLM-compatible seam.
- Digest assembly/index: `AssembledDigest`, `DigestAssembler`, `DigestIndexStore`.
- Delivery rendering first pass: `TelegramDigestRenderer` formats digest messages and splits at item boundaries.
- State docs exist and are current: `PROGRESS.md`, `DIGEST.md`, `DECISIONS.md`.

## Tested

- `. .venv/bin/activate && pytest -q` passes (23 tests).
- `. .venv/bin/activate && pytest -m e2e -q` passes.
- `. .venv/bin/activate && ruff check .` passes.
- `. .venv/bin/activate && mypy src` passes.

## Next

Stage 9: feedback processor + slash command behavior via fakes. Start with button feedback updating pref tables and `/sources`, `/cost`, `/prefs export` skeleton commands.

## Open

- Full chat SPEC could not be found on disk at the Telegram cache path inside this runtime; repo `SPEC.md` currently has a placeholder.
- Real Anthropic SDK and cassette recorder are not built yet.
- Subscription-window budget calibration is not implemented yet; current budget enforcer covers per-run caps.
- Optional cheap-LLM tie-breaker in §8.4 is not built yet.
- Real Telegram reader, session login, bot process/buttons, feedback learning, daily review, CLI dryrun/cost, and docs/handover are pending.
- No GitHub remote/auth configured yet; user wants GitHub connection postponed until tomorrow night.
- No live Telegram/BotFather access is authorised or implemented.
- Must keep updating `PROGRESS.md` after each task and `DIGEST.md` at each stage gate.
