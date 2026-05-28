import asyncio
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tg_digest.types import RawMessage


class LiveAccessNotAuthorized(RuntimeError):
    """Raised when code attempts to create a live Telegram client before a gate opens."""


@dataclass(frozen=True)
class TelegramReaderConfig:
    api_id: int
    api_hash: str
    allowed_sources: list[str]
    session_path: Path | None = None
    mark_as_read: bool = False
    download_media: bool = False

    def build_live_reader(self, *, authorised: bool) -> "TelethonReaderAdapter":
        if not authorised:
            raise LiveAccessNotAuthorized(
                "Live Telegram reader access is gated until the user authorises it."
            )
        return TelethonReaderAdapter(validate_reader_config(self))


def validate_reader_config(config: TelegramReaderConfig) -> TelegramReaderConfig:
    if not config.allowed_sources:
        raise ValueError("Telegram reader requires a non-empty allowlist")
    refused = [source for source in config.allowed_sources if source.startswith("me:")]
    if refused:
        raise ValueError("Telegram reader refuses private/1:1 sources by default")
    return config


class TelethonReaderAdapter:
    """Lazy live-reader adapter; imports Telethon only when live gates are open."""

    def __init__(
        self,
        config: TelegramReaderConfig,
        *,
        client_factory: Callable[[str, int, str], Any] | None = None,
    ) -> None:
        self.config = validate_reader_config(config)
        self._client: Any | None = None
        self._client_factory = client_factory

    def client(self) -> Any:
        if self._client is None:
            session = str(self.config.session_path or "tg-digest-reader")
            if self._client_factory is not None:
                self._client = self._client_factory(
                    session, self.config.api_id, self.config.api_hash
                )
            else:
                try:
                    from telethon import TelegramClient  # type: ignore[import-not-found]
                except ImportError as exc:
                    raise RuntimeError(
                        "telethon is required for live Telegram reading; install the live extra."
                    ) from exc
                self._client = TelegramClient(session, self.config.api_id, self.config.api_hash)
        return self._client

    def fetch_recent(self, *, limit_per_source: int) -> list[RawMessage]:
        """Fetch recent messages from explicitly allowlisted sources without read acks/media."""

        if limit_per_source < 1:
            raise ValueError("limit_per_source must be positive")
        return asyncio.run(self._fetch_recent_async(limit_per_source=limit_per_source))

    async def _fetch_recent_async(self, *, limit_per_source: int) -> list[RawMessage]:
        client = self.client()
        rows: list[RawMessage] = []
        async with client:
            for source in self.config.allowed_sources:
                async for message in client.iter_messages(source, limit=limit_per_source):
                    text = str(
                        getattr(message, "message", None)
                        or getattr(message, "text", "")
                        or ""
                    )
                    msg_id = int(message.id)
                    date = _message_date_iso(getattr(message, "date", None))
                    rows.append(
                        RawMessage(
                            source_id=_source_id(source),
                            msg_id=msg_id,
                            date=date,
                            text=text,
                            links=_extract_links(text),
                        )
                    )
        return rows


def _source_id(source: str) -> str:
    return source.removeprefix("@").replace("/", "_").replace("-", "_")


def _message_date_iso(value: Any) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return str(value.isoformat())
    return datetime.now(UTC).isoformat()


def _extract_links(text: str) -> list[str]:
    return re.findall(r"https?://[^\s)\]>]+", text)
