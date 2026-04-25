from pathlib import Path

import pytest

from tg_digest.integrations.telegram_reader import (
    LiveAccessNotAuthorized,
    TelegramReaderConfig,
    validate_reader_config,
)


def test_reader_config_requires_explicit_allowlist_and_refuses_private_sources() -> None:
    with pytest.raises(ValueError, match="allowlist"):
        validate_reader_config(TelegramReaderConfig(api_id=1, api_hash="h", allowed_sources=[]))

    with pytest.raises(ValueError, match="private"):
        validate_reader_config(
            TelegramReaderConfig(api_id=1, api_hash="h", allowed_sources=["me:private"])
        )


def test_reader_config_defaults_to_read_only_and_no_media_downloads() -> None:
    config = validate_reader_config(
        TelegramReaderConfig(api_id=1, api_hash="h", allowed_sources=["@public_channel"])
    )

    assert config.mark_as_read is False
    assert config.download_media is False
    assert config.allowed_sources == ["@public_channel"]


def test_live_reader_factory_is_gated_until_user_authorises(tmp_path: Path) -> None:
    config = TelegramReaderConfig(
        api_id=1,
        api_hash="h",
        allowed_sources=["@public_channel"],
        session_path=tmp_path / "reader.session",
    )

    with pytest.raises(LiveAccessNotAuthorized):
        config.build_live_reader(authorised=False)
