from tg_digest.filter_cluster.core import Cluster
from tg_digest.scorer.core import ScoredCluster, Scorer, SelectBudget
from tg_digest.types import RawMessage


def make_scored(item_id: int, text: str) -> ScoredCluster:
    message = RawMessage(
        source_id="s",
        msg_id=item_id,
        date="2026-04-25T00:00:00Z",
        text=text,
    )
    return ScoredCluster(
        cluster=Cluster(messages=[message], representative=message, traction=1),
        score=0.5,
    )


def test_optional_tie_breaker_orders_equal_score_known_items() -> None:
    low = make_scored(1, "ordinary update")
    high = make_scored(2, "breaking important update")
    scorer = Scorer(
        tie_breaker=lambda item: 1.0
        if "important" in item.cluster.representative.text
        else 0.0
    )

    selected = scorer.select(
        [low, high],
        SelectBudget(
            known_ratio_of_surviving=1.0,
            floor=1,
            cap=1,
            exploration_ratio=0.0,
        ),
    )

    assert selected[0].cluster.representative.msg_id == 2
