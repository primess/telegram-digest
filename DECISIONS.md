# tg-digest Decisions

## 2026-04-24 — Repository location

Context: User asked to implement from Telegram in local WSL/container.
Decision: Create source repository at `/root/tg-digest`.
Consequences: Future agents should resume there; runtime default remains `~/.tg-digest` per spec.

Stage 10 local implementation (2026-04-25T20:45Z):
- GitHub SSH deploy-key write access still fails in this Hermes sandbox because OpenSSH rejects bind-mounted config/key ownership; continued using public HTTPS clone and will commit locally only.
- Preference learning is implemented fake-first/no-network in tg_digest.learning.preferences and integrated into feedback button handling; live Telegram gates remain closed.
