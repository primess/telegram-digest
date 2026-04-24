import json
from pathlib import Path

from tg_digest.testbed.fakes import BudgetSimulator, ClockFake, FakeBot, FakeLLM, FakeReader
from tg_digest.types import Prompt, SourceInfo


def test_fake_reader_replays_jsonl_without_marking_read(tmp_path: Path) -> None:
    fixture = tmp_path / "messages.jsonl"
    fixture.write_text(
        json.dumps(
            {
                "source_id": "verge",
                "msg_id": 1,
                "date": "2026-04-24T09:00:00+03:00",
                "text": "hello world from telegram digest",
                "links": ["https://example.com"],
            }
        )
        + "\n"
    )
    reader = FakeReader(fixture)

    messages = list(
        reader.fetch_messages(
            SourceInfo(id="verge", kind="channel", handle="@verge", topics=["tech"]),
            since_msg_id=None,
            limit=10,
            mark_as_read=False,
        )
    )

    assert messages[0].msg_id == 1
    assert messages[0].links == ["https://example.com"]
    assert reader.read_ack_calls == []


def test_fake_llm_echo_returns_accounted_response() -> None:
    llm = FakeLLM(mode="echo")

    response = llm.complete(
        Prompt(system="summarise", user="abcdef"), model="fake", max_output_tokens=20
    )

    assert response.text.startswith("abcdef")
    assert response.input_tokens > 0
    assert response.output_tokens > 0


def test_fake_bot_records_digest_artifact(tmp_path: Path) -> None:
    bot = FakeBot(artifact_dir=tmp_path)

    receipt = bot.deliver_text("run-1", "Digest body")

    assert receipt.ok is True
    assert (tmp_path / "digest-run-1.md").read_text() == "Digest body"


def test_clock_fake_and_budget_simulator_exercise_hard_stop() -> None:
    clock = ClockFake("2026-04-24T09:00:00+03:00")
    budget = BudgetSimulator(input_cap=100, output_cap=50, clock=clock)

    budget.record(input_tokens=80, output_tokens=10)
    assert budget.would_exceed(input_tokens=21, output_tokens=0) is True
    assert budget.would_exceed(input_tokens=20, output_tokens=40) is False
