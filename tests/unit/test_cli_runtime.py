import json
from pathlib import Path

from typer.testing import CliRunner

from tg_digest.cli import app


def write_fixture(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "source_id": "boi",
                        "msg_id": 1,
                        "date": "2026-04-25T09:00:00+00:00",
                        "text": "Bank of Israel published a rates update",
                        "links": ["https://example.test/rates"],
                    }
                ),
                json.dumps(
                    {
                        "source_id": "fed",
                        "msg_id": 2,
                        "date": "2026-04-25T09:05:00+00:00",
                        "text": "Fed officials discussed inflation risks",
                        "links": [],
                    }
                ),
            ]
        )
    )


def test_dryrun_uses_fixture_and_writes_artifact_without_network(tmp_path: Path) -> None:
    fixture = tmp_path / "messages.jsonl"
    home = tmp_path / "home"
    write_fixture(fixture)

    result = CliRunner().invoke(
        app,
        ["dryrun", "--home", str(home), "--fixture", str(fixture), "--run-id", "r1"],
    )

    assert result.exit_code == 0
    assert "Dry run complete" in result.stdout
    assert "selected=2" in result.stdout
    artifact = home / "artifacts" / "digest-r1.md"
    assert artifact.exists()
    assert "Bank of Israel" in artifact.read_text()


def test_status_reports_runtime_state_after_bootstrap(tmp_path: Path) -> None:
    home = tmp_path / "home"
    dryrun = CliRunner().invoke(app, ["dryrun", "--home", str(home), "--run-id", "r2"])
    assert dryrun.exit_code == 0

    result = CliRunner().invoke(app, ["status", "--home", str(home)])

    assert result.exit_code == 0
    assert "Status: ok" in result.stdout
    assert "runs=1" in result.stdout
    assert "digest_items=1" in result.stdout


def test_cost_reports_llm_usage_summary(tmp_path: Path) -> None:
    home = tmp_path / "home"
    dryrun = CliRunner().invoke(app, ["dryrun", "--home", str(home), "--run-id", "r3"])
    assert dryrun.exit_code == 0

    result = CliRunner().invoke(app, ["cost", "--home", str(home)])

    assert result.exit_code == 0
    assert "Cost:" in result.stdout
    assert "input_tokens=" in result.stdout
    assert "output_tokens=" in result.stdout
