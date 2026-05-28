import json
from pathlib import Path

from typer.testing import CliRunner

from tg_digest.cli import app


def test_run_once_reports_pipeline_stages_from_sources_fixture(tmp_path: Path) -> None:
    sources = tmp_path / "sources.yaml"
    fixture = tmp_path / "messages.jsonl"
    home = tmp_path / "home"
    sources.write_text(
        """
version: 1
defaults:
  mark_as_read: never
sources:
  - id: tech_one
    kind: channel
    handle: "@tech_one"
    topics: [Tech]
  - id: israel_one
    kind: channel
    handle: "@israel_one"
    topics: [Israel News]
""".strip()
    )
    fixture.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "source_id": "tech_one",
                        "msg_id": 11,
                        "date": "2026-05-28T10:00:00+00:00",
                        "text": (
                            "OpenAI released a significant developer platform update for agents."
                        ),
                        "links": ["https://example.test/agents"],
                    }
                ),
                json.dumps(
                    {
                        "source_id": "tech_one",
                        "msg_id": 12,
                        "date": "2026-05-28T10:01:00+00:00",
                        "text": (
                            "OpenAI released a significant developer platform update for agents."
                        ),
                        "links": [],
                    }
                ),
                json.dumps(
                    {
                        "source_id": "israel_one",
                        "msg_id": 21,
                        "date": "2026-05-28T10:02:00+00:00",
                        "text": "ממשלת ישראל פרסמה הודעה ביטחונית חשובה לציבור הרחב.",
                        "links": [],
                    }
                ),
                json.dumps(
                    {
                        "source_id": "israel_one",
                        "msg_id": 22,
                        "date": "2026-05-28T10:03:00+00:00",
                        "text": "short",
                        "links": [],
                    }
                ),
            ]
        )
        + "\n"
    )

    result = CliRunner().invoke(
        app,
        [
            "run-once",
            "--sources",
            str(sources),
            "--home",
            str(home),
            "--run-id",
            "debug1",
            "--fixture-client",
            str(fixture),
            "--limit-per-source",
            "10",
            "--select-floor",
            "1",
            "--select-cap",
            "2",
        ],
    )

    assert result.exit_code == 0
    assert "Run once complete" in result.stdout
    assert "sources=2" in result.stdout
    assert "fetched=4" in result.stdout
    assert "filtered=2" in result.stdout
    assert "clusters=2" in result.stdout
    assert "selected=1" in result.stdout
    assert (home / "artifacts" / "run-debug1-debug.json").exists()
    digest = home / "artifacts" / "digest-debug1.md"
    assert digest.exists()
    assert "debug1-01" in digest.read_text()

    debug = json.loads((home / "artifacts" / "run-debug1-debug.json").read_text())
    assert debug["counts"] == {
        "sources": 2,
        "fetched": 4,
        "filtered": 2,
        "clusters": 2,
        "scored": 2,
        "selected": 1,
        "summarized": 1,
    }
    assert len(debug["filtering"]["dropped"]) == 2
    assert len(debug["scoring"]["top"] ) == 2
    assert len(debug["summaries"]) == 1
