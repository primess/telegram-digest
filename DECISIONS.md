# tg-digest Decisions

## 2026-04-24 — Repository location

Context: User asked to implement from Telegram in local WSL/container.
Decision: Create source repository at `/root/tg-digest`.
Consequences: Future agents should resume there; runtime default remains `~/.tg-digest` per spec.

Stage 10 local implementation (2026-04-25T20:45Z):
- GitHub SSH deploy-key write access still fails in this Hermes sandbox because OpenSSH rejects bind-mounted config/key ownership; continued using public HTTPS clone and will commit locally only.
- Preference learning is implemented fake-first/no-network in tg_digest.learning.preferences and integrated into feedback button handling; live Telegram gates remain closed.

Stage 11-13 local implementation (2026-04-25T20:53Z):
- Implemented CLI dryrun/status/cost using only local fixtures, fakes, SQLite, and local artifacts; no live Telegram endpoint touched.
- Implemented Telegram reader and bot integration seams as safety-gated/no-network units because live endpoint gates are not authorised.
- Added optional deterministic scorer tie-breaker seam instead of live cheap-LLM calls.

Stage 12 live-smoke local configuration (2026-05-28):
- Store Telegram API credentials only in local `.env`, which is git-ignored; commit only `.env.example`.
- Allow `tg-digest telegram-smoke` to load `.env` automatically so the live smoke command does not need secrets on the command line.
- Keep read-only source allowlist in `sources.yaml`; current smoke source is public channel `@hadshotiran`.
