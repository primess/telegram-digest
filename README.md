# tg-digest

Local, read-only Telegram digest pipeline for explicitly allowlisted public sources.

## Quickstart (current implementation state)

```bash
cd /root/tg-digest
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
ruff check .
mypy src
```

Live Telegram and BotFather connections are gated and intentionally not implemented before fake E2E tests are green.

## Resume order

1. Read `DIGEST.md` for current state.
2. Read `PROGRESS.md` for the next task.
3. Read `SPEC.md` for full requirements.
