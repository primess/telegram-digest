from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


class SourceConfigError(ValueError):
    """Raised when sources.yaml violates tg-digest safety rules."""


MarkAsRead = Literal["never", "always", "inherit"]
SourceKind = Literal["channel", "group", "topic"]


class SourceDefaults(BaseModel):
    mark_as_read: MarkAsRead = "never"
    language_hint: str = "auto"
    enabled: bool = True
    weight: float = Field(default=1.0, ge=0.0, le=2.0)


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: SourceKind
    handle: str
    topics: list[str] = Field(default_factory=list)
    topic_id: int | None = None
    mark_as_read: MarkAsRead | None = None
    language_hint: str | None = None
    enabled: bool | None = None
    weight: float | None = Field(default=None, ge=0.0, le=2.0)

    @field_validator("id")
    @classmethod
    def id_must_be_slug(cls, value: str) -> str:
        import re

        if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", value):
            raise ValueError(
                "source id must be slug-cased with lowercase letters, numbers, underscores"
            )
        return value

    @model_validator(mode="after")
    def topic_requires_topic_id(self) -> "Source":
        if self.kind == "topic" and self.topic_id is None:
            raise ValueError("kind: topic requires topic_id")
        return self

    def with_defaults(self, defaults: SourceDefaults) -> "ResolvedSource":
        return ResolvedSource(
            id=self.id,
            kind=self.kind,
            handle=self.handle,
            topics=self.topics,
            topic_id=self.topic_id,
            mark_as_read=self.mark_as_read or defaults.mark_as_read,
            language_hint=self.language_hint or defaults.language_hint,
            enabled=defaults.enabled if self.enabled is None else self.enabled,
            weight=defaults.weight if self.weight is None else self.weight,
        )


class ResolvedSource(BaseModel):
    id: str
    kind: SourceKind
    handle: str
    topics: list[str]
    topic_id: int | None
    mark_as_read: MarkAsRead
    language_hint: str
    enabled: bool
    weight: float


class SourcesConfig(BaseModel):
    version: Literal[1]
    defaults: SourceDefaults = Field(default_factory=SourceDefaults)
    sources: list[ResolvedSource]


def _parse_sources(raw: object) -> SourcesConfig:
    if not isinstance(raw, dict):
        raise SourceConfigError("sources.yaml must contain a mapping")
    try:
        defaults = SourceDefaults.model_validate(raw.get("defaults") or {})
        raw_sources = raw.get("sources") or []
        if not isinstance(raw_sources, list):
            raise SourceConfigError("sources must be a list")
        seen_ids: set[str] = set()
        seen_handles: set[str] = set()
        sources: list[ResolvedSource] = []
        for item in raw_sources:
            src = Source.model_validate(item)
            if src.id in seen_ids:
                raise SourceConfigError(f"Duplicate source id: {src.id}")
            if src.handle in seen_handles:
                raise SourceConfigError(f"Duplicate handle: {src.handle}")
            seen_ids.add(src.id)
            seen_handles.add(src.handle)
            sources.append(src.with_defaults(defaults))
        version = raw.get("version")
        if version != 1:
            raise SourceConfigError("sources.yaml version must be 1")
        return SourcesConfig(version=1, defaults=defaults, sources=sources)
    except ValidationError as exc:
        message = str(exc)
        if "kind" in message:
            message += "; v1 only supports public channel/group/topic sources"
        raise SourceConfigError(message) from exc


def load_sources_config(path: Path) -> SourcesConfig:
    """Load and validate an allowlist-only sources.yaml file."""

    return _parse_sources(yaml.safe_load(path.read_text()))
