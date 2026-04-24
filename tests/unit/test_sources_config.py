from pathlib import Path

import pytest

from tg_digest.config.sources import SourceConfigError, load_sources_config


def write_yaml(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "sources.yaml"
    path.write_text(content)
    return path


def test_sources_defaults_and_valid_public_channel(tmp_path: Path) -> None:
    path = write_yaml(
        tmp_path,
        """
version: 1
defaults:
  mark_as_read: never
  language_hint: auto
  enabled: true
  weight: 1.0
sources:
  - id: verge
    kind: channel
    handle: "@verge"
    topics: [tech, news]
""",
    )

    config = load_sources_config(path)

    assert config.version == 1
    assert config.sources[0].id == "verge"
    assert config.sources[0].mark_as_read == "never"
    assert config.sources[0].language_hint == "auto"
    assert config.sources[0].enabled is True
    assert config.sources[0].weight == 1.0


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("id: verge", "id: Verge Bad"),
        ("kind: channel", "kind: topic"),
    ],
)
def test_source_validation_refuses_bad_slug_and_topic_without_topic_id(
    tmp_path: Path, field: str, replacement: str
) -> None:
    base = """
version: 1
defaults: {}
sources:
  - id: verge
    kind: channel
    handle: "@verge"
    topics: [tech]
"""
    text = base.replace(field, replacement)
    path = write_yaml(tmp_path, text)

    with pytest.raises(SourceConfigError):
        load_sources_config(path)


def test_source_validation_refuses_duplicate_handles(tmp_path: Path) -> None:
    path = write_yaml(
        tmp_path,
        """
version: 1
defaults: {}
sources:
  - id: verge
    kind: channel
    handle: "@verge"
    topics: [tech]
  - id: verge2
    kind: channel
    handle: "@verge"
    topics: [tech]
""",
    )

    with pytest.raises(SourceConfigError, match="Duplicate handle"):
        load_sources_config(path)


def test_source_validation_refuses_private_or_1to1_sources(tmp_path: Path) -> None:
    path = write_yaml(
        tmp_path,
        """
version: 1
defaults: {}
sources:
  - id: private_chat
    kind: private
    handle: "@someone"
    topics: [dm]
""",
    )

    with pytest.raises(SourceConfigError, match="public channel/group/topic"):
        load_sources_config(path)
