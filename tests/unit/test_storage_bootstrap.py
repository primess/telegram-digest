import sqlite3
import stat
from pathlib import Path

from tg_digest.storage.bootstrap import REQUIRED_TABLES, bootstrap_home


def test_bootstrap_creates_runtime_dirs_with_private_permissions(tmp_path: Path) -> None:
    home = tmp_path / "tg-home"

    bootstrap_home(home)

    for name in ["config", "secrets", "session", "logs"]:
        path = home / name
        assert path.is_dir()
    assert stat.S_IMODE((home / "session").stat().st_mode) == 0o700
    assert stat.S_IMODE((home / "secrets").stat().st_mode) == 0o700


def test_bootstrap_creates_required_sqlite_tables(tmp_path: Path) -> None:
    home = tmp_path / "tg-home"

    db_path = bootstrap_home(home)

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("select name from sqlite_master where type='table'").fetchall()
    table_names = {row[0] for row in rows}
    assert set(REQUIRED_TABLES).issubset(table_names)
