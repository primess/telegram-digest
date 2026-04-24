# tg-digest State Digest

## Built

- Repository scaffold exists at `/root/tg-digest`.
- Python package skeleton under `src/tg_digest`.
- Typer CLI entrypoint with `tg-digest version`.
- State docs exist: `PROGRESS.md`, `DIGEST.md`, `DECISIONS.md`.

## Tested

- `. .venv/bin/activate && pytest -q` passes.
- `. .venv/bin/activate && ruff check .` passes.
- `. .venv/bin/activate && mypy src` passes.

## Next

Stage 1: implement config/source validation and SQLite bootstrap using strict TDD.

## Open

- Full chat SPEC could not be found on disk at the Telegram cache path inside this runtime; repo `SPEC.md` currently has a placeholder.
- No live Telegram/BotFather access is authorised or implemented.
- Must keep updating `PROGRESS.md` after each task and `DIGEST.md` at each stage gate.
