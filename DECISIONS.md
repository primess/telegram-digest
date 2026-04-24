# tg-digest Decisions

## 2026-04-24 — Repository location

Context: User asked to implement from Telegram in local WSL/container.
Decision: Create source repository at `/root/tg-digest`.
Consequences: Future agents should resume there; runtime default remains `~/.tg-digest` per spec.
