from collections.abc import Callable
from dataclasses import dataclass

from tg_digest.filter_cluster.core import Cluster


@dataclass(frozen=True)
class ScoringWeights:
    source_weight: float = 0.25
    topic_match: float = 0.2
    keyword_match: float = 0.15
    traction: float = 0.2
    recency: float = 0.0
    length_fit: float = 0.1
    novelty: float = 0.1
    feedback_history: float = 0.0


@dataclass(frozen=True)
class ScoringContext:
    source_weights: dict[str, float]
    topic_weights: dict[str, float]
    keyword_weights: dict[str, float]
    source_topics: dict[str, list[str]]


@dataclass(frozen=True)
class SelectBudget:
    known_ratio_of_surviving: float = 0.08
    floor: int = 5
    cap: int = 25
    exploration_ratio: float = 0.15


@dataclass(frozen=True)
class ScoredCluster:
    cluster: Cluster
    score: float
    kind: str = "known"
    selection_reason: str = ""
    novelty: float = 0.0


class Scorer:
    def __init__(
        self,
        weights: ScoringWeights | None = None,
        tie_breaker: Callable[[ScoredCluster], float] | None = None,
    ) -> None:
        self.weights = weights or ScoringWeights()
        self.tie_breaker = tie_breaker

    def score(self, clusters: list[Cluster], ctx: ScoringContext) -> list[ScoredCluster]:
        if not clusters:
            return []
        max_traction = max(cluster.traction for cluster in clusters) or 1.0
        scored = []
        for cluster in clusters:
            source_id = cluster.representative.source_id
            text = cluster.representative.text.lower()
            topics = ctx.source_topics.get(source_id, [])
            topic_score = max([ctx.topic_weights.get(topic, 0.0) for topic in topics] or [0.0])
            keyword_score = max(
                [weight for term, weight in ctx.keyword_weights.items() if term.lower() in text]
                or [0.0]
            )
            source_score = min(ctx.source_weights.get(source_id, 1.0) / 2.0, 1.0)
            traction_score = min(cluster.traction / max_traction, 1.0)
            length_score = min(len(cluster.representative.text) / 240.0, 1.0)
            raw = (
                self.weights.source_weight * source_score
                + self.weights.topic_match * clamp01(topic_score)
                + self.weights.keyword_match * clamp01(keyword_score)
                + self.weights.traction * traction_score
                + self.weights.length_fit * length_score
            )
            reasons = [f"source:{source_id}"]
            reasons.extend(
                f"topic:{topic}" for topic in topics if ctx.topic_weights.get(topic, 0) > 0
            )
            scored.append(
                ScoredCluster(
                    cluster=cluster,
                    score=clamp01(raw),
                    selection_reason=" + ".join(reasons),
                    novelty=0.0,
                )
            )
        return scored

    def select(self, scored: list[ScoredCluster], budget: SelectBudget) -> list[ScoredCluster]:
        if not scored:
            return []
        total_target = int(len(scored) * budget.known_ratio_of_surviving)
        total_target = max(budget.floor, total_target)
        total_target = min(budget.cap, total_target, len(scored))
        exploration_count = int(total_target * budget.exploration_ratio)
        if budget.exploration_ratio > 0 and exploration_count == 0 and total_target > 1:
            exploration_count = 1
        known_count = total_target - exploration_count

        by_score = sorted(scored, key=self._selection_key, reverse=True)
        selected_known = by_score[:known_count]
        selected_ids = {id(item) for item in selected_known}
        exploration_pool = [item for item in scored if id(item) not in selected_ids]
        exploration_pool.sort(
            key=lambda item: (item.novelty, item.cluster.traction, item.score),
            reverse=True,
        )
        selected_exploration = [
            ScoredCluster(
                cluster=item.cluster,
                score=item.score,
                kind="exploration",
                selection_reason=item.selection_reason or "exploration",
                novelty=item.novelty,
            )
            for item in exploration_pool[:exploration_count]
        ]
        return selected_known + selected_exploration

    def _selection_key(self, item: ScoredCluster) -> tuple[float, float]:
        tiebreak = 0.0 if self.tie_breaker is None else self.tie_breaker(item)
        return (item.score, tiebreak)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
