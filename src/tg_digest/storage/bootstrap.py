import os
import sqlite3
from pathlib import Path

REQUIRED_TABLES = (
    "seen_messages",
    "clusters",
    "run_log",
    "digest_index",
    "pref_topics",
    "pref_sources",
    "pref_keywords",
    "pref_patterns",
    "feedback_log",
    "llm_usage",
)

_SCHEMA = [
    """create table if not exists seen_messages (
        source_id text not null,
        msg_id integer not null,
        date text not null,
        text_hash text not null,
        normalized_text text not null,
        expires_at text not null,
        primary key (source_id, msg_id)
    )""",
    """create table if not exists clusters (
        cluster_id text primary key,
        representative_source_id text not null,
        representative_msg_id integer not null,
        score real,
        created_at text not null,
        expires_at text not null
    )""",
    """create table if not exists run_log (
        run_id text primary key,
        started_at text not null,
        finished_at text,
        status text not null,
        counts_json text not null default '{}',
        cost_json text not null default '{}'
    )""",
    """create table if not exists digest_index (
        item_id text primary key,
        digest_id text not null,
        item_json text not null,
        created_at text not null,
        expires_at text not null
    )""",
    """create table if not exists pref_topics (
        topic text primary key,
        weight real not null,
        updated_at text not null
    )""",
    """create table if not exists pref_sources (
        source_id text primary key,
        weight real not null,
        muted_until text,
        updated_at text not null
    )""",
    """create table if not exists pref_keywords (
        term text primary key,
        weight real not null,
        hits integer not null default 0,
        updated_at text not null
    )""",
    """create table if not exists pref_patterns (
        pattern_id text primary key,
        description text not null,
        weight real not null
    )""",
    """create table if not exists feedback_log (
        item_id text not null,
        signal text not null,
        ts text not null
    )""",
    """create table if not exists llm_usage (
        run_id text not null,
        call_id text not null,
        model text not null,
        purpose text not null default '',
        input_tokens integer not null,
        output_tokens integer not null,
        est_cost_usd real not null,
        ts text not null,
        primary key (run_id, call_id)
    )""",
]


def _mkdir_private(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)


def bootstrap_home(home: Path) -> Path:
    """Create tg-digest runtime directories and initialize state.db."""

    home.mkdir(parents=True, exist_ok=True)
    for name in ("config", "logs"):
        (home / name).mkdir(exist_ok=True)
    for name in ("secrets", "session"):
        _mkdir_private(home / name)

    db_path = home / "state.db"
    with sqlite3.connect(db_path) as conn:
        for statement in _SCHEMA:
            conn.execute(statement)
        conn.commit()
    return db_path
