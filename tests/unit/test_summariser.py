from tg_digest.filter_cluster.core import Cluster
from tg_digest.scorer.core import ScoredCluster
from tg_digest.summariser.core import Summariser
from tg_digest.testbed.fakes import FakeLLM
from tg_digest.types import RawMessage


def test_summariser_returns_digest_items_with_links_and_deeplinks() -> None:
    message = RawMessage(
        source_id="boi",
        msg_id=123,
        date="2026-04-24T09:00:00+03:00",
        text="Bank of Israel published an interest-rate update for markets.",
        links=["https://example.com/rates"],
    )
    scored = ScoredCluster(
        cluster=Cluster(messages=[message], representative=message, traction=1.0),
        score=0.81,
        kind="known",
        selection_reason="topic:markets + source:boi",
    )
    summariser = Summariser(FakeLLM(mode="echo"), model="fake-haiku")

    items = summariser.summarise([scored], digest_id="d2604")

    assert items[0].item_id == "d2604-01"
    assert items[0].summary.endswith("[FAKE]")
    assert items[0].links == ["https://example.com/rates"]
    assert items[0].telegram_deeplinks == ["https://t.me/boi/123"]
    assert items[0].flags == []
