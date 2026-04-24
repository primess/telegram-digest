from tg_digest.filter_cluster.core import FilterCluster, FilterConfig
from tg_digest.types import RawMessage


def msg(msg_id: int, text: str, source_id: str = "src") -> RawMessage:
    return RawMessage(
        source_id=source_id,
        msg_id=msg_id,
        date="2026-04-24T09:00:00+03:00",
        text=text,
        links=[],
    )


def test_filter_drops_near_empty_media_duplicates_blacklist_and_language_mismatch() -> None:
    fc = FilterCluster(
        FilterConfig(min_chars=20, languages=["en", "he"], blacklist_keywords=["casino"])
    )
    messages = [
        msg(1, "short"),
        msg(2, ""),
        msg(3, "This is a substantial English update about markets."),
        msg(4, "This is a substantial English update about markets."),
        msg(5, "This casino promotion is definitely long enough."),
        msg(6, "Ceci est un long message en francais sur les marches."),
        msg(7, "זהו עדכון עברי משמעותי על ריבית ושווקים."),
    ]

    kept = fc.filter(messages)

    assert [item.msg_id for item in kept] == [3, 7]


def test_cluster_groups_similar_messages_and_tracks_traction() -> None:
    fc = FilterCluster(FilterConfig(min_chars=1, languages=["en"]))
    messages = [
        msg(1, "Bank of Israel rate decision moves markets today", "a"),
        msg(2, "Bank of Israel rate decision moves markets today with details", "b"),
        msg(3, "New GPU benchmark results released for developers", "c"),
    ]

    clusters = fc.cluster(messages)

    assert len(clusters) == 2
    merged = max(clusters, key=lambda cluster: cluster.traction)
    assert [item.msg_id for item in merged.messages] == [1, 2]
    assert merged.representative.msg_id == 2
    assert merged.traction == 2.0
