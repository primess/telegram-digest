from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class SourceInfo:
    id: str
    kind: Literal["channel", "group", "topic"]
    handle: str
    topics: list[str]


@dataclass(frozen=True)
class RawMessage:
    source_id: str
    msg_id: int
    date: str
    text: str
    links: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Prompt:
    system: str
    user: str


@dataclass(frozen=True)
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    cost_estimate_usd: float = 0.0


@dataclass(frozen=True)
class DeliveryReceipt:
    ok: bool
    artifact_path: str | None = None


@dataclass(frozen=True)
class DigestItem:
    item_id: str
    source_ids: list[str]
    summary: str
    links: list[str]
    telegram_deeplinks: list[str]
    flags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Digest:
    digest_id: str
    generated_at: str
    counts: dict[str, int]
    items: list[DigestItem]
