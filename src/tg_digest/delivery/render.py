from tg_digest.digest.assembly import AssembledDigest


class TelegramDigestRenderer:
    def __init__(self, max_chars: int = 4096) -> None:
        self.max_chars = max_chars

    def render(self, digest: AssembledDigest) -> list[str]:
        chunks: list[str] = [f"Digest {digest.digest_id}\n"]
        for index, item in enumerate(digest.items, start=1):
            block = self._render_item(index, item)
            if len(chunks[-1]) + len(block) + 1 > self.max_chars and chunks[-1].strip():
                chunks.append(block)
            else:
                chunks[-1] = f"{chunks[-1]}\n{block}".strip()
        stats = self._render_stats(digest)
        if len(chunks[-1]) + len(stats) + 1 > self.max_chars:
            chunks.append(stats)
        else:
            chunks[-1] = f"{chunks[-1]}\n\n{stats}"
        return chunks

    def _render_item(self, index: int, item: dict[str, object]) -> str:
        links = as_list(item.get("links"))
        deeplinks = as_list(item.get("telegram_deeplinks"))
        raw_score = item.get("score", 0.0)
        score = raw_score if isinstance(raw_score, int | float) else 0.0
        header = f"#{index:02d} · {item.get('kind', 'known')} · score {score:.2f}"
        lines = [
            header,
            str(item.get("summary", "")),
        ]
        lines.extend(str(link) for link in links)
        lines.extend(f"🔗 {link}" for link in deeplinks)
        reason = item.get("selection_reason", "")
        if reason:
            lines.append(f"why: {reason}")
        lines.append("Feedback: 👍 More / 👎 Less / 🔇 Mute source / 📌 Save")
        return "\n".join(lines)

    def _render_stats(self, digest: AssembledDigest) -> str:
        counts = digest.counts
        budget = digest.budget
        return (
            "Counts: "
            f"fetched={counts.get('fetched', 0)} "
            f"post_filter={counts.get('post_filter', 0)} "
            f"clusters={counts.get('clusters', 0)} "
            f"selected={counts.get('selected', 0)}\n"
            "Cost: "
            f"input={budget.get('input_tokens', 0)} "
            f"output={budget.get('output_tokens', 0)} "
            f"usd={budget.get('cost_usd_est', 0)}"
        )


def as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    return []
