from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tg_digest.integrations.telegram_reader import TelegramReaderConfig, TelethonReaderAdapter


class FakeTelegramMessage:
    def __init__(self, msg_id: int, text: str) -> None:
        self.id = msg_id
        self.message = text
        self.date = datetime(2026, 5, 28, 9, 0, tzinfo=UTC)


class FakeTelegramClient:
    def __init__(self, session: str, api_id: int, api_hash: str) -> None:
        self.session = session
        self.api_id = api_id
        self.api_hash = api_hash
        self.requested: list[tuple[str, int]] = []

    async def __aenter__(self) -> "FakeTelegramClient":
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    async def iter_messages(self, source: str, *, limit: int) -> Any:
        self.requested.append((source, limit))
        for index in range(limit):
            yield FakeTelegramMessage(
                msg_id=100 + index,
                text=f"Update from {source}: https://example.test/{index}",
            )


def test_adapter_fetch_recent_collects_allowlisted_messages(
    tmp_path: Path,
) -> None:
    created: list[FakeTelegramClient] = []

    def factory(session: str, api_id: int, api_hash: str) -> FakeTelegramClient:
        client = FakeTelegramClient(session, api_id, api_hash)
        created.append(client)
        return client

    adapter = TelethonReaderAdapter(
        TelegramReaderConfig(
            api_id=123,
            api_hash="hash",
            allowed_sources=["@one", "@two"],
            session_path=tmp_path / "reader.session",
        ),
        client_factory=factory,
    )

    messages = adapter.fetch_recent(limit_per_source=2)

    assert len(messages) == 4
    assert {message.source_id for message in messages} == {"one", "two"}
    assert messages[0].links == ["https://example.test/0"]
    assert created[0].requested == [("@one", 2), ("@two", 2)]
    assert adapter.config.mark_as_read is False
    assert adapter.config.download_media is False
