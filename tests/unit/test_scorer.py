from tg_digest.filter_cluster.core import Cluster
from tg_digest.scorer.core import (
    ScoredCluster,
    Scorer,
    ScoringContext,
    ScoringWeights,
    SelectBudget,
)
from tg_digest.types import RawMessage


def msg(msg_id: int, text: str, source_id: str = "src") -> RawMessage:
    return RawMessage(source_id, msg_id, "2026-04-24T09:00:00+03:00", text, [])


def cluster(msg_id: int, text: str, source_id: str = "src", traction: float = 1.0) -> Cluster:
    message = msg(msg_id, text, source_id)
    return Cluster(messages=[message], representative=message, traction=traction)


def test_scorer_combines_source_topic_keyword_traction_and_length() -> None:
    scorer = Scorer(
        ScoringWeights(
            source_weight=0.3,
            topic_match=0.2,
            keyword_match=0.2,
            traction=0.2,
            length_fit=0.1,
        )
    )
    ctx = ScoringContext(
        source_weights={"boi": 1.5},
        topic_weights={"markets": 1.0},
        keyword_weights={"rates": 1.0},
        source_topics={"boi": ["markets"]},
    )

    scored = scorer.score([cluster(1, "rates " * 40, "boi", traction=3)], ctx)

    assert len(scored) == 1
    assert 0.70 <= scored[0].score <= 1.0
    assert "source:boi" in scored[0].selection_reason
    assert "topic:markets" in scored[0].selection_reason


def test_selector_uses_percentage_floor_cap_and_exploration_slots() -> None:
    scored = [
        ScoredCluster(cluster=cluster(i, f"message {i}"), score=1 - (i / 100), kind="known")
        for i in range(1, 21)
    ]
    # Low-score high-traction novel item should be pulled into exploration.
    scored.append(
        ScoredCluster(
            cluster=cluster(99, "novel high traction", "newsrc", traction=10),
            score=0.05,
            kind="known",
            novelty=1.0,
        )
    )
    scorer = Scorer()

    selected = scorer.select(
        scored,
        SelectBudget(known_ratio_of_surviving=0.2, floor=5, cap=6, exploration_ratio=0.2),
    )

    assert len(selected) == 5
    assert selected[-1].kind == "exploration"
    assert selected[-1].cluster.representative.msg_id == 99
