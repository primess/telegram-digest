from dataclasses import dataclass
from pathlib import Path
from typing import Any


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

    def __init__(self, config: TelegramReaderConfig) -> None:
        self.config = validate_reader_config(config)
        self._client: Any | None = None

    def client(self) -> Any:
        if self._client is None:
            try:
                from telethon import TelegramClient  # type: ignore[import-not-found]
            except ImportError as exc:
                raise RuntimeError(
                    "telethon is required for live Telegram reading; install the live extra."
                ) from exc
            session = str(self.config.session_path or "tg-digest-reader")
            self._client = TelegramClient(session, self.config.api_id, self.config.api_hash)
        return self._client
