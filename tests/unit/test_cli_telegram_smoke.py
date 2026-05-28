import json
from pathlib import Path

from typer.testing import CliRunner

from tg_digest.cli import app


def test_telegram_smoke_refuses_to_run_without_explicit_authorisation(tmp_path: Path) -> None:
    artifact = tmp_path / "messages.jsonl"

    result = CliRunner().invoke(
        app,
        [
            "telegram-smoke",
            "--api-id",
            "123",
            "--api-hash",
            "hash",
            "--allow-source",
            "@public_channel",
            "--artifact",
            str(artifact),
        ],
    )

    assert result.exit_code != 0
    assert "requires --i-authorize-live-read" in result.stdout
    assert not artifact.exists()


def _write_fixture(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "source_id": "public_channel",
                "msg_id": 10,
                "date": "2026-05-28T09:00:00+00:00",
                "text": "Read-only smoke item https://example.test/item",
                "links": ["https://example.test/item"],
            }
        )
        + "\n"
    )


def test_telegram_smoke_can_use_fixture_client_for_no_network_test(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.jsonl"
    artifact = tmp_path / "messages.jsonl"
    _write_fixture(fixture)

    result = CliRunner().invoke(
        app,
        [
            "telegram-smoke",
            "--api-id",
            "123",
            "--api-hash",
            "hash",
            "--allow-source",
            "@public_channel",
            "--artifact",
            str(artifact),
            "--i-authorize-live-read",
            "--fixture-client",
            str(fixture),
        ],
    )

    assert result.exit_code == 0
    assert "Telegram read-only smoke complete" in result.stdout
    assert "messages=1" in result.stdout
    assert artifact.exists()
    assert "Read-only smoke item" in artifact.read_text()


def test_telegram_smoke_loads_api_credentials_from_dotenv(
    tmp_path: Path, monkeypatch: object
) -> None:
    fixture = tmp_path / "fixture.jsonl"
    artifact = tmp_path / "messages.jsonl"
    _write_fixture(fixture)
    (tmp_path / ".env").write_text(
        "TG_DIGEST_API_ID=123\nTG_DIGEST_API_HASH=hash-from-dotenv\n"
    )
    monkeypatch.chdir(tmp_path)  # type: ignore[attr-defined]
    monkeypatch.delenv("TG_DIGEST_API_ID", raising=False)  # type: ignore[attr-defined]
    monkeypatch.delenv("TG_DIGEST_API_HASH", raising=False)  # type: ignore[attr-defined]

    result = CliRunner().invoke(
        app,
        [
            "telegram-smoke",
            "--allow-source",
            "@public_channel",
            "--artifact",
            str(artifact),
            "--i-authorize-live-read",
            "--fixture-client",
            str(fixture),
        ],
    )

    assert result.exit_code == 0
    assert "Telegram read-only smoke complete" in result.stdout
    assert artifact.exists()
