import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from tg_digest.types import DigestItem


@dataclass(frozen=True)
class AssembledDigest:
    digest_id: str
    generated_at: str
    window: dict[str, str]
    counts: dict[str, int]
    budget: dict[str, float | int]
    items: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "digest_id": self.digest_id,
            "generated_at": self.generated_at,
            "window": self.window,
            "counts": self.counts,
            "budget": self.budget,
            "items": self.items,
        }


class DigestAssembler:
    def assemble(
        self,
        *,
        digest_id: str,
        generated_at: str,
        window: dict[str, str],
        counts: dict[str, int],
        budget: dict[str, float | int],
        items: list[DigestItem],
        item_meta: dict[str, dict[str, Any]],
    ) -> AssembledDigest:
        assembled_items = []
        for item in items:
            meta = item_meta.get(item.item_id, {})
            assembled_items.append(
                {
                    "item_id": item.item_id,
                    "kind": meta.get("kind", "known"),
                    "score": meta.get("score", 0.0),
                    "selection_reason": meta.get("selection_reason", ""),
                    "source_ids": item.source_ids,
                    "summary": item.summary,
                    "links": item.links,
                    "telegram_deeplinks": item.telegram_deeplinks,
                    "flags": item.flags,
                }
            )
        return AssembledDigest(
            digest_id=digest_id,
            generated_at=generated_at,
            window=window,
            counts=counts,
            budget=budget,
            items=assembled_items,
        )


class DigestIndexStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._ensure_table()

    def persist(self, digest: AssembledDigest) -> None:
        created_at = digest.generated_at
        expires_at = (datetime.now(UTC) + timedelta(days=30)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            for item in digest.items:
                conn.execute(
                    """insert or replace into digest_index
                    (item_id, digest_id, item_json, created_at, expires_at)
                    values (?, ?, ?, ?, ?)""",
                    (
                        item["item_id"],
                        digest.digest_id,
                        json.dumps(item, ensure_ascii=False),
                        created_at,
                        expires_at,
                    ),
                )
            conn.commit()

    def resolve_item(self, item_id: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "select item_json from digest_index where item_id = ?",
                (item_id,),
            ).fetchone()
        if row is None:
            return None
        data: dict[str, Any] = json.loads(row[0])
        return data

    def _ensure_table(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """create table if not exists digest_index (
                    item_id text primary key,
                    digest_id text not null,
                    item_json text not null,
                    created_at text not null,
                    expires_at text not null
                )"""
            )
            conn.commit()
