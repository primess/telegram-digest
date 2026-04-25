import json
import sqlite3
from pathlib import Path

from tg_digest.learning.preferences import (
    FeedbackSignal,
    PreferenceLearner,
    ReviewSampler,
    ema_alpha,
    ema_update,
)
from tg_digest.storage.bootstrap import bootstrap_home


def test_ema_alpha_and_update_respect_half_life() -> None:
    assert ema_alpha(age_steps=0, half_life_steps=4) == 1.0
    assert ema_alpha(age_steps=4, half_life_steps=4) == 0.5
    assert ema_update(current=0.2, observation=1.0, age_steps=4, half_life_steps=4) == 0.6


def test_exploration_negative_signal_is_damped_but_positive_is_not(tmp_path: Path) -> None:
    db_path = bootstrap_home(tmp_path / "home")
    learner = PreferenceLearner(db_path, half_life_steps=1)

    learner.apply(
        FeedbackSignal(
            source_ids=["boi"],
            topics=["markets"],
            direction=-1.0,
            item_kind="exploration",
        )
    )
    learner.apply(
        FeedbackSignal(
            source_ids=["fed"],
            topics=["macro"],
            direction=1.0,
            item_kind="exploration",
        )
    )

    with sqlite3.connect(db_path) as conn:
        boi_weight = conn.execute(
            "select weight from pref_sources where source_id = 'boi'"
        ).fetchone()[0]
        markets_weight = conn.execute(
            "select weight from pref_topics where topic = 'markets'"
        ).fetchone()[0]
        fed_weight = conn.execute(
            "select weight from pref_sources where source_id = 'fed'"
        ).fetchone()[0]
        macro_weight = conn.execute(
            "select weight from pref_topics where topic = 'macro'"
        ).fetchone()[0]

    assert boi_weight == -0.3
    assert markets_weight == -0.3
    assert fed_weight == 1.0
    assert macro_weight == 1.0


def test_known_negative_signal_is_not_damped(tmp_path: Path) -> None:
    db_path = bootstrap_home(tmp_path / "home")
    learner = PreferenceLearner(db_path, half_life_steps=1)

    learner.apply(
        FeedbackSignal(
            source_ids=["boi"],
            topics=["markets"],
            direction=-1.0,
            item_kind="known",
        )
    )

    with sqlite3.connect(db_path) as conn:
        source_weight = conn.execute(
            "select weight from pref_sources where source_id = 'boi'"
        ).fetchone()[0]
        topic_weight = conn.execute(
            "select weight from pref_topics where topic = 'markets'"
        ).fetchone()[0]

    assert source_weight == -1.0
    assert topic_weight == -1.0


def test_review_sampler_returns_ignored_recent_items_oldest_first(tmp_path: Path) -> None:
    db_path = bootstrap_home(tmp_path / "home")
    with sqlite3.connect(db_path) as conn:
        for item_id, created_at in [
            ("old", "2026-04-20T09:00:00+00:00"),
            ("recent_ignored", "2026-04-24T09:00:00+00:00"),
            ("recent_feedback", "2026-04-24T10:00:00+00:00"),
            ("newest_ignored", "2026-04-24T11:00:00+00:00"),
        ]:
            conn.execute(
                """insert into digest_index
                (item_id, digest_id, item_json, created_at, expires_at)
                values (?, ?, ?, ?, ?)""",
                (
                    item_id,
                    "d1",
                    json.dumps({"item_id": item_id, "summary": item_id}),
                    created_at,
                    "2026-05-24T09:00:00+00:00",
                ),
            )
        conn.execute(
            "insert into feedback_log (item_id, signal, ts) values (?, ?, ?)",
            ("recent_feedback", "more", "2026-04-24T10:30:00+00:00"),
        )
        conn.commit()

    sampler = ReviewSampler(db_path)
    items = sampler.sample_ignored_recent(
        now="2026-04-25T09:00:00+00:00", lookback_days=2, limit=2
    )

    assert [item.item_id for item in items] == ["recent_ignored", "newest_ignored"]
    assert items[0].item_json["summary"] == "recent_ignored"
