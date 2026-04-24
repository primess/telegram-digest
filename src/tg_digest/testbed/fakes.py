import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from tg_digest.types import DeliveryReceipt, LLMResponse, Prompt, RawMessage, SourceInfo


class FakeReader:
    """Reader fake that replays JSONL fixtures and never touches the network."""

    def __init__(self, fixture_path: Path) -> None:
        self.fixture_path = fixture_path
        self.read_ack_calls: list[tuple[str, int]] = []

    def list_sources(self) -> list[SourceInfo]:
        source_ids = {message.source_id for message in self._messages()}
        return [
            SourceInfo(id=source_id, kind="channel", handle=f"@{source_id}", topics=[])
            for source_id in sorted(source_ids)
        ]

    def fetch_messages(
        self,
        source: SourceInfo,
        since_msg_id: int | None,
        limit: int,
        mark_as_read: bool,
    ) -> list[RawMessage]:
        messages = [
            message
            for message in self._messages()
            if message.source_id == source.id
            and (since_msg_id is None or message.msg_id > since_msg_id)
        ][:limit]
        if mark_as_read:
            self.read_ack_calls.extend((source.id, message.msg_id) for message in messages)
        return messages

    def resolve_deeplink(self, msg: RawMessage) -> str:
        return f"https://t.me/{msg.source_id}/{msg.msg_id}"

    def _messages(self) -> list[RawMessage]:
        rows = []
        for line in self.fixture_path.read_text().splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            rows.append(
                RawMessage(
                    source_id=data["source_id"],
                    msg_id=int(data["msg_id"]),
                    date=data["date"],
                    text=data["text"],
                    links=list(data.get("links", [])),
                )
            )
        return rows


class FakeLLM:
    def __init__(
        self, mode: Literal["echo", "canned"] = "echo", canned: dict[str, str] | None = None
    ) -> None:
        self.mode = mode
        self.canned = canned or {}
        self.calls: list[Prompt] = []

    def complete(self, prompt: Prompt, *, model: str, max_output_tokens: int) -> LLMResponse:
        del model
        self.calls.append(prompt)
        if self.mode == "canned" and prompt.user in self.canned:
            text = self.canned[prompt.user]
        else:
            text = f"{prompt.user[:max_output_tokens]} [FAKE]"
        return LLMResponse(
            text=text,
            input_tokens=max(1, len(prompt.system.split()) + len(prompt.user.split())),
            output_tokens=max(1, len(text.split())),
        )


class FakeBot:
    def __init__(self, artifact_dir: Path) -> None:
        self.artifact_dir = artifact_dir
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    def deliver_text(self, run_id: str, body: str) -> DeliveryReceipt:
        path = self.artifact_dir / f"digest-{run_id}.md"
        path.write_text(body)
        return DeliveryReceipt(ok=True, artifact_path=str(path))


class ClockFake:
    def __init__(self, iso_now: str) -> None:
        self._now = datetime.fromisoformat(iso_now)

    def now(self) -> datetime:
        return self._now

    def advance(self, **kwargs: float) -> None:
        self._now += timedelta(**kwargs)


class BudgetSimulator:
    def __init__(self, input_cap: int, output_cap: int, clock: ClockFake) -> None:
        self.input_cap = input_cap
        self.output_cap = output_cap
        self.clock = clock
        self.input_used = 0
        self.output_used = 0
        self.events: list[dict[str, int | str]] = []

    def record(self, *, input_tokens: int, output_tokens: int) -> None:
        self.input_used += input_tokens
        self.output_used += output_tokens
        self.events.append(
            {
                "ts": self.clock.now().isoformat(),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
        )

    def would_exceed(self, *, input_tokens: int, output_tokens: int) -> bool:
        return (
            self.input_used + input_tokens > self.input_cap
            or self.output_used + output_tokens > self.output_cap
        )
