import json
import sqlite3
from pathlib import Path

from tg_digest.feedback.processor import FeedbackProcessor
from tg_digest.storage.bootstrap import bootstrap_home


def seed_digest_item(
    db_path: Path, *, item_id: str = "d2604-01", kind: str = "known"
) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """insert into digest_index
            (item_id, digest_id, item_json, created_at, expires_at)
            values (?, ?, ?, ?, ?)""",
            (
                item_id,
                "d2604",
                json.dumps(
                    {
                        "item_id": item_id,
                        "source_ids": ["boi"],
                        "summary": "Rates update",
                        "links": [],
                        "telegram_deeplinks": [],
                        "flags": [],
                        "topics": ["markets"],
                        "kind": kind,
                    }
                ),
                "2026-04-24T09:00:00+03:00",
                "2026-05-24T09:00:00+03:00",
            ),
        )
        conn.commit()


def test_button_more_updates_source_topic_and_feedback_log(tmp_path: Path) -> None:
    db_path = bootstrap_home(tmp_path / "home")
    seed_digest_item(db_path)
    processor = FeedbackProcessor(db_path)

    processor.ingest_button("d2604-01", "more", user_id=123)

    with sqlite3.connect(db_path) as conn:
        source_weight = conn.execute(
            "select weight from pref_sources where source_id = 'boi'"
        ).fetchone()[0]
        topic_weight = conn.execute(
            "select weight from pref_topics where topic = 'markets'"
        ).fetchone()[0]
        signal = conn.execute("select signal from feedback_log").fetchone()[0]
    assert source_weight > 0
    assert topic_weight > 0
    assert signal == "more"


def test_exploration_less_button_uses_damped_preference_learning(tmp_path: Path) -> None:
    db_path = bootstrap_home(tmp_path / "home")
    seed_digest_item(db_path, item_id="explore-01", kind="exploration")
    processor = FeedbackProcessor(db_path)

    processor.ingest_button("explore-01", "less", user_id=123)

    with sqlite3.connect(db_path) as conn:
        source_weight = conn.execute(
            "select weight from pref_sources where source_id = 'boi'"
        ).fetchone()[0]
        topic_weight = conn.execute(
            "select weight from pref_topics where topic = 'markets'"
        ).fetchone()[0]
    assert source_weight == -0.3
    assert topic_weight == -0.3


def test_mute_command_sets_muted_until_and_unmute_clears_it(tmp_path: Path) -> None:
    db_path = bootstrap_home(tmp_path / "home")
    processor = FeedbackProcessor(db_path)

    muted = processor.ingest_command("/mute boi 3", user_id=123)
    unmuted = processor.ingest_command("/unmute boi", user_id=123)

    assert "Muted boi" in muted.message
    assert "Unmuted boi" in unmuted.message
    with sqlite3.connect(db_path) as conn:
        muted_until = conn.execute(
            "select muted_until from pref_sources where source_id = 'boi'"
        ).fetchone()[0]
    assert muted_until is None


def test_prefs_export_and_reset_commands(tmp_path: Path) -> None:
    db_path = bootstrap_home(tmp_path / "home")
    processor = FeedbackProcessor(db_path)
    processor.ingest_command("/topic markets +", user_id=123)

    exported = processor.ingest_command("/prefs export", user_id=123)
    reset = processor.ingest_command("/prefs reset topics", user_id=123)

    assert "markets" in exported.message
    assert "Reset topics" in reset.message
    with sqlite3.connect(db_path) as conn:
        count = conn.execute("select count(*) from pref_topics").fetchone()[0]
    assert count == 0


def test_sources_topics_cost_and_dryrun_commands_return_status(tmp_path: Path) -> None:
    db_path = bootstrap_home(tmp_path / "home")
    processor = FeedbackProcessor(db_path)

    assert "Sources" in processor.ingest_command("/sources", user_id=123).message
    assert "Topics" in processor.ingest_command("/topics", user_id=123).message
    assert "Cost" in processor.ingest_command("/cost today", user_id=123).message
    assert "Dry run" in processor.ingest_command("/dryrun", user_id=123).message
