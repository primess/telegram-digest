# tg-digest State Digest

## Completion estimate

- Stage-count estimate: 10 of 16 stages (0–9) are implemented/gated locally: about 63%.
- V1 deliverable checklist estimate: about 52% complete. Core deterministic pipeline, fakes, digest assembly/rendering, and feedback command skeleton exist; real Telegram/bot, full preference learning/review, CLI/dryrun, live smoke tests, and final docs are still pending.
- Codex quota policy: user asked to pause at 92% weekly; after user reported quota prediction dropped to 81%, one additional stage was completed.

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
- Feedback processor first pass: button signals update prefs/logs; slash command skeleton covers mute/unmute/topic/topics/sources/prefs/cost/dryrun/digest/status.
- State docs exist and are current: `PROGRESS.md`, `DIGEST.md`, `DECISIONS.md`.

## Tested

- `. .venv/bin/activate && pytest -q` passes (27 tests).
- `. .venv/bin/activate && pytest -m e2e -q` passes.
- `. .venv/bin/activate && ruff check .` passes.
- `. .venv/bin/activate && mypy src` passes.

## Next

Stage 10: preference learning + daily review. Implement EMA half-life utilities, exploration negative damping, positive non-damping, and review-session sampling over ignored recent items.

## Open

- Full chat SPEC could not be found on disk at the Telegram cache path inside this runtime; repo `SPEC.md` currently has a placeholder.
- Real Anthropic SDK and cassette recorder are not built yet.
- Subscription-window budget calibration is not implemented yet; current budget enforcer covers per-run caps.
- Optional cheap-LLM tie-breaker in §8.4 is not built yet.
- Real Telegram reader, session login, bot process/buttons, full preference learning/review, CLI dryrun/cost, and docs/handover are pending.
- No GitHub remote/auth configured yet; user wants GitHub connection postponed until tomorrow night.
- No live Telegram/BotFather access is authorised or implemented.
- Must keep updating `PROGRESS.md` after each task and `DIGEST.md` at each stage gate.
