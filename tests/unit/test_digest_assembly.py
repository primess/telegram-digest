import sqlite3
from pathlib import Path

from tg_digest.digest.assembly import DigestAssembler, DigestIndexStore
from tg_digest.types import DigestItem


def item(item_id: str) -> DigestItem:
    return DigestItem(
        item_id=item_id,
        source_ids=["boi"],
        summary="Interest-rate update summary",
        links=["https://example.com/rates"],
        telegram_deeplinks=["https://t.me/boi/123"],
        flags=[],
    )


def test_digest_assembler_builds_spec_shape() -> None:
    digest = DigestAssembler().assemble(
        digest_id="d2604",
        generated_at="2026-04-24T09:00:00+03:00",
        window={"from": "2026-04-24T00:00:00+03:00", "to": "2026-04-24T09:00:00+03:00"},
        counts={"fetched": 10, "post_filter": 8, "clusters": 6, "selected": 1},
        budget={"input_tokens": 100, "output_tokens": 20, "cost_usd_est": 0.001},
        items=[item("d2604-01")],
        item_meta={
            "d2604-01": {"kind": "known", "score": 0.81, "selection_reason": "topic:markets"}
        },
    )

    data = digest.to_dict()

    assert data["digest_id"] == "d2604"
    assert data["window"]["from"].startswith("2026-04-24")
    assert data["counts"]["selected"] == 1
    assert data["budget"]["input_tokens"] == 100
    assert data["items"][0]["item_id"] == "d2604-01"
    assert data["items"][0]["kind"] == "known"
    assert data["items"][0]["score"] == 0.81
    assert data["items"][0]["selection_reason"] == "topic:markets"


def test_digest_index_persists_and_resolves_callback_items(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    store = DigestIndexStore(db_path)
    digest = DigestAssembler().assemble(
        digest_id="d2604",
        generated_at="2026-04-24T09:00:00+03:00",
        window={"from": "a", "to": "b"},
        counts={"fetched": 1, "post_filter": 1, "clusters": 1, "selected": 1},
        budget={"input_tokens": 1, "output_tokens": 1, "cost_usd_est": 0.0},
        items=[item("d2604-01")],
        item_meta={"d2604-01": {"kind": "known", "score": 0.5, "selection_reason": "source:boi"}},
    )

    store.persist(digest)

    resolved = store.resolve_item("d2604-01")
    assert resolved is not None
    assert resolved["summary"] == "Interest-rate update summary"
    with sqlite3.connect(db_path) as conn:
        count = conn.execute("select count(*) from digest_index").fetchone()[0]
    assert count == 1
