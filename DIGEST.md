# tg-digest State Digest

## Completion estimate

- Stage-count estimate: 14 of 16 stages (0–13) are implemented/gated locally: about 88%.
- V1 deliverable checklist estimate: about 78% complete. Core deterministic pipeline, fakes, digest assembly/rendering, feedback command skeleton, preference learning/review helpers, CLI dry-run/cost/status, Telegram reader safety gate, bot dispatcher seam, and optional scorer tie-breaker exist; live Telegram smoke tests, Hermes scheduling, and final handover docs are still pending.
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
- Preference learning/review first pass: EMA half-life utilities, feedback application to source/topic prefs, exploration negative-signal damping, positive exploration non-damping, and ignored-recent review sampling.
- CLI runtime first pass: `dryrun`, `status`, and `cost` commands run no-network fixture/fake flows, persist run/digest/usage state, and produce local artifacts.
- Live integration seams first pass: Telegram reader config validation/live gate, lazy Telethon adapter, pure bot callback/command dispatcher, and optional scorer tie-breaker.
- State docs exist and are current: `PROGRESS.md`, `DIGEST.md`, `DECISIONS.md`.

## Tested

- `. .venv/bin/activate && pytest -q` passes (42 tests).
- `. .venv/bin/activate && pytest -m e2e -q` passes.
- `. .venv/bin/activate && ruff check .` passes.
- `. .venv/bin/activate && mypy src` passes (31 source files).

## Next

Stage 14/15: Hermes scheduling integration and final handover docs. Live Telegram/BotFather smoke tests remain gated until explicitly authorised.

## Open

- Full chat SPEC could not be found on disk at the Telegram cache path inside this runtime; repo `SPEC.md` currently has a placeholder.
- Real Anthropic SDK is not built yet; current LLM path remains fake/accounted only.
- Subscription-window budget calibration is not implemented yet; current budget enforcer covers per-run caps.
- Live Telegram smoke tests, Hermes scheduling integration, and final docs/handover remain pending.
- GitHub repo is public at `https://github.com/primess/telegram-digest`; HTTPS read/clone works in Hermes. SSH deploy-key write access is still not fixed in the sandbox, so this stage is committed locally only until SSH mount/permissions are resolved.
- No live Telegram/BotFather access is authorised or implemented.
- Must keep updating `PROGRESS.md` after each task and `DIGEST.md` at each stage gate.
