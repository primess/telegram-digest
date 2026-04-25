import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal, cast

from tg_digest.learning.preferences import FeedbackSignal, PreferenceLearner


@dataclass(frozen=True)
class CommandResult:
    message: str


class FeedbackProcessor:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def ingest_button(self, item_id: str, signal: str, user_id: int) -> None:
        del user_id
        item = self._resolve_item(item_id)
        direction = 1.0 if signal == "more" else -1.0 if signal == "less" else 0.0
        if signal == "mute_source":
            for source_id in item.get("source_ids", []):
                self._mute_source(str(source_id), days=7)
        elif direction != 0.0:
            item_kind = "exploration" if item.get("kind") == "exploration" else "known"
            PreferenceLearner(self.db_path).apply(
                FeedbackSignal(
                    source_ids=[str(source_id) for source_id in item.get("source_ids", [])],
                    topics=[str(topic) for topic in item.get("topics", [])],
                    direction=direction,
                    item_kind=cast(Literal["known", "exploration"], item_kind),
                )
            )
        self._log_feedback(item_id, signal)

    def ingest_command(self, cmd: str, user_id: int) -> CommandResult:
        del user_id
        parts = cmd.strip().split()
        if not parts:
            return CommandResult("Empty command")
        name = parts[0].lower()
        if name == "/mute" and len(parts) >= 2:
            days = 7
            if len(parts) >= 3 and parts[2] != "perm":
                days = int(parts[2])
            self._mute_source(
                parts[1], days=None if len(parts) >= 3 and parts[2] == "perm" else days
            )
            return CommandResult(f"Muted {parts[1]}")
        if name == "/unmute" and len(parts) >= 2:
            self._unmute_source(parts[1])
            return CommandResult(f"Unmuted {parts[1]}")
        if name == "/topic" and len(parts) >= 3:
            delta = 0.2 if parts[2] == "+" else -0.2 if parts[2] == "-" else 0.0
            if parts[2] == "reset":
                self._reset_topic(parts[1])
            else:
                self._nudge_topic(parts[1], delta)
            return CommandResult(f"Updated topic {parts[1]}")
        if name == "/topics":
            return CommandResult(
                "Topics:\n" + json.dumps(self._export_table("pref_topics"), ensure_ascii=False)
            )
        if name == "/sources":
            return CommandResult(
                "Sources:\n" + json.dumps(self._export_table("pref_sources"), ensure_ascii=False)
            )
        if name == "/prefs" and len(parts) >= 2 and parts[1] == "export":
            return CommandResult(
                json.dumps(self.export_prefs(), ensure_ascii=False, sort_keys=True)
            )
        if name == "/prefs" and len(parts) >= 3 and parts[1] == "reset":
            self.reset_prefs(parts[2])
            return CommandResult(f"Reset {parts[2]}")
        if name == "/cost":
            return CommandResult("Cost: " + json.dumps(self._cost_summary(), sort_keys=True))
        if name == "/dryrun":
            return CommandResult("Dry run requested; scheduler/CLI will execute no-LLM preview.")
        if name == "/digest":
            return CommandResult("Digest run requested; scheduler/CLI will trigger pipeline.")
        if name == "/status":
            return CommandResult("Status: feedback processor online")
        return CommandResult("Unknown command")

    def export_prefs(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "topics": self._export_table("pref_topics"),
            "sources": self._export_table("pref_sources"),
            "keywords": self._export_table("pref_keywords"),
            "patterns": self._export_table("pref_patterns"),
        }

    def reset_prefs(self, scope: str) -> None:
        tables = {
            "all": ["pref_topics", "pref_sources", "pref_keywords", "pref_patterns"],
            "topics": ["pref_topics"],
            "sources": ["pref_sources"],
            "keywords": ["pref_keywords"],
        }.get(scope, [])
        with sqlite3.connect(self.db_path) as conn:
            for table in tables:
                conn.execute(f"delete from {table}")
            conn.commit()

    def _resolve_item(self, item_id: str) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "select item_json from digest_index where item_id = ?", (item_id,)
            ).fetchone()
        if row is None:
            raise ValueError(f"Unknown digest item: {item_id}")
        return dict(json.loads(row[0]))

    def _nudge_source(self, source_id: str, delta: float) -> None:
        self._upsert_weight("pref_sources", "source_id", source_id, delta, extra_muted=False)

    def _nudge_topic(self, topic: str, delta: float) -> None:
        self._upsert_weight("pref_topics", "topic", topic, delta, extra_muted=False)

    def _reset_topic(self, topic: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("delete from pref_topics where topic = ?", (topic,))
            conn.commit()

    def _upsert_weight(
        self, table: str, key_col: str, key: str, delta: float, *, extra_muted: bool
    ) -> None:
        del extra_muted
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(f"select weight from {table} where {key_col} = ?", (key,)).fetchone()
            new_weight = max(-1.0, min(1.0, (float(row[0]) if row else 0.0) + delta))
            if row:
                conn.execute(
                    f"update {table} set weight = ?, updated_at = ? where {key_col} = ?",
                    (new_weight, now, key),
                )
            else:
                if table == "pref_sources":
                    conn.execute(
                        """insert into pref_sources
                        (source_id, weight, muted_until, updated_at)
                        values (?, ?, ?, ?)""",
                        (key, new_weight, None, now),
                    )
                else:
                    conn.execute(
                        f"insert into {table} ({key_col}, weight, updated_at) values (?, ?, ?)",
                        (key, new_weight, now),
                    )
            conn.commit()

    def _mute_source(self, source_id: str, days: int | None) -> None:
        muted_until = (
            None if days is None else (datetime.now(UTC) + timedelta(days=days)).isoformat()
        )
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """insert into pref_sources (source_id, weight, muted_until, updated_at)
                values (?, ?, ?, ?)
                on conflict(source_id) do update set muted_until = excluded.muted_until,
                weight = min(pref_sources.weight, excluded.weight),
                updated_at = excluded.updated_at""",
                (source_id, -1.0, muted_until, now),
            )
            conn.commit()

    def _unmute_source(self, source_id: str) -> None:
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """insert into pref_sources (source_id, weight, muted_until, updated_at)
                values (?, ?, ?, ?)
                on conflict(source_id) do update set muted_until = null,
                updated_at = excluded.updated_at""",
                (source_id, 0.0, None, now),
            )
            conn.commit()

    def _log_feedback(self, item_id: str, signal: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "insert into feedback_log (item_id, signal, ts) values (?, ?, ?)",
                (item_id, signal, datetime.now(UTC).isoformat()),
            )
            conn.commit()

    def _export_table(self, table: str) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.execute(f"select * from {table}").fetchall()]

    def _cost_summary(self) -> dict[str, int | float]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """select coalesce(sum(input_tokens), 0),
                coalesce(sum(output_tokens), 0),
                coalesce(sum(est_cost_usd), 0) from llm_usage"""
            ).fetchone()
        return {
            "input_tokens": int(row[0]),
            "output_tokens": int(row[1]),
            "cost_usd_est": float(row[2]),
        }
