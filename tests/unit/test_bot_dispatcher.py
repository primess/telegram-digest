import json
import sqlite3
from pathlib import Path

from tg_digest.bot.dispatcher import BotDispatcher, CallbackResult
from tg_digest.storage.bootstrap import bootstrap_home


def seed_item(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """insert into digest_index
            (item_id, digest_id, item_json, created_at, expires_at)
            values (?, ?, ?, ?, ?)""",
            (
                "d1-01",
                "d1",
                json.dumps(
                    {
                        "item_id": "d1-01",
                        "source_ids": ["boi"],
                        "topics": ["markets"],
                        "summary": "Rates",
                        "kind": "known",
                    }
                ),
                "2026-04-25T09:00:00+00:00",
                "2026-05-25T09:00:00+00:00",
            ),
        )
        conn.commit()


def test_callback_dispatcher_routes_feedback_without_network(tmp_path: Path) -> None:
    db_path = bootstrap_home(tmp_path / "home")
    seed_item(db_path)
    dispatcher = BotDispatcher(db_path)

    result = dispatcher.handle_callback("more:d1-01", user_id=123)

    assert result == CallbackResult(ok=True, message="Recorded more for d1-01")
    with sqlite3.connect(db_path) as conn:
        signal = conn.execute("select signal from feedback_log").fetchone()[0]
    assert signal == "more"


def test_callback_dispatcher_rejects_malformed_callback(tmp_path: Path) -> None:
    db_path = bootstrap_home(tmp_path / "home")
    dispatcher = BotDispatcher(db_path)

    result = dispatcher.handle_callback("bad-format", user_id=123)

    assert result.ok is False
    assert "Malformed" in result.message


def test_command_dispatcher_reuses_feedback_processor(tmp_path: Path) -> None:
    db_path = bootstrap_home(tmp_path / "home")
    dispatcher = BotDispatcher(db_path)

    result = dispatcher.handle_command("/mute boi 3", user_id=123)

    assert result.ok is True
    assert "Muted boi" in result.message
