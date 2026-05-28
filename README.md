# tg-digest

Local, read-only Telegram digest pipeline for explicitly allowlisted public sources.

## Quickstart (current implementation state)

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
ruff check .
mypy src
```

For the authorised read-only Telegram smoke, install the live extra and provide Telegram API credentials:

```bash
pip install -e '.[dev,live]'
export TG_DIGEST_API_ID='<api_id>'
export TG_DIGEST_API_HASH='<api_hash>'
tg-digest telegram-smoke \
  --i-authorize-live-read \
  --allow-source '@public_channel_or_group' \
  --limit-per-source 3 \
  --artifact .tg-digest/artifacts/telegram-smoke.jsonl
```

The smoke command keeps `mark_as_read=False`, does not download media, and only reads explicitly allowlisted sources.

Live Telegram and BotFather connections are gated and intentionally not implemented before fake E2E tests are green.

## Resume order

1. Read `DIGEST.md` for current state.
2. Read `PROGRESS.md` for the next task.
3. Read `SPEC.md` for full requirements.
