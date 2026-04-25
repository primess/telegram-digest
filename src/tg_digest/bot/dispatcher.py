from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from tg_digest.feedback.processor import FeedbackProcessor


@dataclass(frozen=True)
class CallbackResult:
    ok: bool
    message: str


class BotDispatcher:
    """Pure dispatcher for Telegram callbacks/commands; no network side effects."""

    _VALID_SIGNALS: ClassVar[set[str]] = {"more", "less", "mute_source"}

    def __init__(self, db_path: Path) -> None:
        self.processor = FeedbackProcessor(db_path)

    def handle_callback(self, callback_data: str, *, user_id: int) -> CallbackResult:
        parts = callback_data.split(":", 1)
        if len(parts) != 2:
            return CallbackResult(False, "Malformed callback")
        signal, item_id = parts
        if signal not in self._VALID_SIGNALS or not item_id:
            return CallbackResult(False, "Malformed callback")
        self.processor.ingest_button(item_id, signal, user_id=user_id)
        return CallbackResult(True, f"Recorded {signal} for {item_id}")

    def handle_command(self, command: str, *, user_id: int) -> CallbackResult:
        result = self.processor.ingest_command(command, user_id=user_id)
        return CallbackResult(True, result.message)
