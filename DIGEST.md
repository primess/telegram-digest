# tg-digest State Digest

## Built

- Repository scaffold exists at `/root/tg-digest`.
- Python package skeleton under `src/tg_digest`.
- Typer CLI entrypoint with `tg-digest version`.
- Config module: `tg_digest.config.sources` loads `sources.yaml`, applies defaults, refuses bad slugs, duplicate handles/ids, unsupported private/1:1 kinds, and `topic` without `topic_id`.
- Storage module: `tg_digest.storage.bootstrap` creates runtime dirs and initializes SQLite tables from §12 plus `llm_usage`.
- Testbed first pass: `FakeReader`, `FakeLLM`, `FakeBot`, `ClockFake`, `BudgetSimulator`.
- Shared dataclasses in `tg_digest.types`.
- Placeholder no-network fake pipeline in `tg_digest.pipeline.fake_pipeline`.
- State docs exist and are current: `PROGRESS.md`, `DIGEST.md`, `DECISIONS.md`.

## Tested

- `. .venv/bin/activate && pytest -q` passes (13 tests).
- `. .venv/bin/activate && pytest -m e2e -q` passes.
- `. .venv/bin/activate && ruff check .` passes.
- `. .venv/bin/activate && mypy src` passes.

## Next

Stage 3: implement deterministic filter + cluster module using strict TDD. Start with `RawMessage` filtering for min chars, language allowlist, blacklist, exact duplicate hash, then add deterministic similarity clustering.

## Open

- Full chat SPEC could not be found on disk at the Telegram cache path inside this runtime; repo `SPEC.md` currently has a placeholder.
- No live Telegram/BotFather access is authorised or implemented.
- Must keep updating `PROGRESS.md` after each task and `DIGEST.md` at each stage gate.
