import json
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal


@dataclass(frozen=True)
class FeedbackSignal:
    source_ids: list[str]
    topics: list[str]
    direction: float
    item_kind: Literal["known", "exploration"] = "known"


@dataclass(frozen=True)
class ReviewItem:
    item_id: str
    created_at: str
    item_json: dict[str, Any]


def ema_alpha(age_steps: int, half_life_steps: int) -> float:
    if half_life_steps <= 0:
        raise ValueError("half_life_steps must be positive")
    if age_steps <= 0:
        return 1.0
    return math.pow(0.5, age_steps / half_life_steps)


def ema_update(
    *, current: float, observation: float, age_steps: int, half_life_steps: int
) -> float:
    alpha = ema_alpha(age_steps=age_steps, half_life_steps=half_life_steps)
    return current * (1.0 - alpha) + observation * alpha


class PreferenceLearner:
    def __init__(self, db_path: Path, *, half_life_steps: int = 14) -> None:
        self.db_path = db_path
        self.half_life_steps = half_life_steps

    def apply(self, signal: FeedbackSignal) -> None:
        observation = self._observation(signal)
        now = datetime.now().astimezone().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            for source_id in signal.source_ids:
                self._upsert_source(conn, source_id, observation, now)
            for topic in signal.topics:
                self._upsert_topic(conn, topic, observation, now)
            conn.commit()

    def _observation(self, signal: FeedbackSignal) -> float:
        direction = max(-1.0, min(1.0, signal.direction))
        if signal.item_kind == "exploration" and direction < 0:
            return direction * 0.3
        return direction

    def _next_weight(self, current: float | None, observation: float) -> float:
        if current is None:
            return max(-1.0, min(1.0, observation))
        updated = ema_update(
            current=current,
            observation=observation,
            age_steps=1,
            half_life_steps=self.half_life_steps,
        )
        return max(-1.0, min(1.0, updated))

    def _upsert_source(
        self, conn: sqlite3.Connection, source_id: str, observation: float, now: str
    ) -> None:
        row = conn.execute(
            "select weight, muted_until from pref_sources where source_id = ?",
            (source_id,),
        ).fetchone()
        weight = self._next_weight(float(row[0]) if row else None, observation)
        muted_until = row[1] if row else None
        conn.execute(
            """insert into pref_sources (source_id, weight, muted_until, updated_at)
            values (?, ?, ?, ?)
            on conflict(source_id) do update set weight = excluded.weight,
            updated_at = excluded.updated_at""",
            (source_id, weight, muted_until, now),
        )

    def _upsert_topic(
        self, conn: sqlite3.Connection, topic: str, observation: float, now: str
    ) -> None:
        row = conn.execute(
            "select weight from pref_topics where topic = ?",
            (topic,),
        ).fetchone()
        weight = self._next_weight(float(row[0]) if row else None, observation)
        conn.execute(
            """insert into pref_topics (topic, weight, updated_at)
            values (?, ?, ?)
            on conflict(topic) do update set weight = excluded.weight,
            updated_at = excluded.updated_at""",
            (topic, weight, now),
        )


class ReviewSampler:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def sample_ignored_recent(
        self, *, now: str, lookback_days: int = 7, limit: int = 10
    ) -> list[ReviewItem]:
        cutoff = datetime.fromisoformat(now) - timedelta(days=lookback_days)
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """select d.item_id, d.created_at, d.item_json
                from digest_index d
                left join feedback_log f on f.item_id = d.item_id
                where f.item_id is null and d.created_at >= ?
                order by d.created_at asc, d.item_id asc
                limit ?""",
                (cutoff.isoformat(), limit),
            ).fetchall()
        return [
            ReviewItem(
                item_id=str(row[0]),
                created_at=str(row[1]),
                item_json=dict(json.loads(row[2])),
            )
            for row in rows
        ]
