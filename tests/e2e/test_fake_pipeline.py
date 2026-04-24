import json
from pathlib import Path

import pytest

from tg_digest.pipeline.fake_pipeline import run_fake_digest
from tg_digest.testbed.fakes import FakeBot, FakeLLM, FakeReader


@pytest.mark.e2e
def test_e2e_fake_pipeline_produces_placeholder_digest_without_network(tmp_path: Path) -> None:
    fixture = tmp_path / "messages.jsonl"
    fixture.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "source_id": "verge",
                        "msg_id": 1,
                        "date": "2026-04-24T09:00:00+03:00",
                        "text": "A substantive technology update about chips and markets.",
                        "links": ["https://example.com/chips"],
                    }
                ),
                json.dumps(
                    {
                        "source_id": "boinews",
                        "msg_id": 2,
                        "date": "2026-04-24T09:05:00+03:00",
                        "text": "עדכון ריבית חשוב מבנק ישראל עם פרטים למשקיעים.",
                        "links": [],
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n"
    )
    artifact_dir = tmp_path / "artifacts"

    digest = run_fake_digest(
        reader=FakeReader(fixture),
        llm=FakeLLM(mode="echo"),
        bot=FakeBot(artifact_dir),
        run_id="e2e-1",
    )

    assert digest.digest_id == "e2e-1"
    assert digest.counts["fetched"] == 2
    assert len(digest.items) == 2
    assert digest.items[0].summary.endswith("[FAKE]")
    assert (artifact_dir / "digest-e2e-1.md").exists()
