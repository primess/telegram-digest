from tg_digest.delivery.render import TelegramDigestRenderer
from tg_digest.digest.assembly import DigestAssembler
from tg_digest.types import DigestItem


def test_renderer_splits_digest_at_item_boundaries_and_includes_stats() -> None:
    digest = DigestAssembler().assemble(
        digest_id="d2604",
        generated_at="2026-04-24T09:00:00+03:00",
        window={"from": "a", "to": "b"},
        counts={"fetched": 10, "post_filter": 8, "clusters": 6, "selected": 2},
        budget={"input_tokens": 100, "output_tokens": 20, "cost_usd_est": 0.001},
        items=[
            DigestItem("d2604-01", ["boi"], "Summary one", ["https://a"], ["https://t.me/boi/1"]),
            DigestItem("d2604-02", ["verge"], "Summary two", [], ["https://t.me/verge/2"]),
        ],
        item_meta={
            "d2604-01": {"kind": "known", "score": 0.81, "selection_reason": "topic:markets"},
            "d2604-02": {"kind": "exploration", "score": 0.42, "selection_reason": "novel"},
        },
    )
    renderer = TelegramDigestRenderer(max_chars=180)

    messages = renderer.render(digest)

    assert len(messages) >= 2
    assert all(len(message) <= 180 for message in messages)
    assert "#01 · known · score 0.81" in "\n".join(messages)
    assert "🔗 https://t.me/boi/1" in "\n".join(messages)
    assert "Counts: fetched=10" in messages[-1]
    assert "Cost: input=100 output=20" in messages[-1]
