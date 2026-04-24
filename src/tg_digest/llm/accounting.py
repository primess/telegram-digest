import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tg_digest.types import LLMResponse, Prompt


@dataclass(frozen=True)
class BudgetLimits:
    per_run_input_token_cap: int = 80_000
    per_run_output_token_cap: int = 20_000


class BudgetExceeded(RuntimeError):
    def __init__(self, message: str, checkpoint: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.checkpoint = checkpoint or {}


class BudgetEnforcer:
    def __init__(self, db_path: Path, limits: BudgetLimits) -> None:
        self.db_path = db_path
        self.limits = limits
        ensure_usage_table(db_path)

    def assert_can_call(
        self,
        *,
        run_id: str,
        estimated_input_tokens: int,
        estimated_output_tokens: int,
        checkpoint: dict[str, Any] | None = None,
    ) -> None:
        used_input, used_output = self.usage_for_run(run_id)
        if used_input + estimated_input_tokens > self.limits.per_run_input_token_cap:
            raise BudgetExceeded("per-run input token cap would be exceeded", checkpoint)
        if used_output + estimated_output_tokens > self.limits.per_run_output_token_cap:
            raise BudgetExceeded("per-run output token cap would be exceeded", checkpoint)

    def usage_for_run(self, run_id: str) -> tuple[int, int]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """select coalesce(sum(input_tokens), 0), coalesce(sum(output_tokens), 0)
                from llm_usage where run_id = ?""",
                (run_id,),
            ).fetchone()
        return int(row[0]), int(row[1])


class AccountedLLM:
    def __init__(self, wrapped: Any, *, db_path: Path, budget: BudgetEnforcer) -> None:
        self.wrapped = wrapped
        self.db_path = db_path
        self.budget = budget
        ensure_usage_table(db_path)

    def complete(
        self,
        prompt: Prompt,
        *,
        model: str,
        max_output_tokens: int,
        run_id: str,
        purpose: str,
        checkpoint: dict[str, Any] | None = None,
    ) -> LLMResponse:
        estimated_input = estimate_tokens(prompt.system) + estimate_tokens(prompt.user)
        self.budget.assert_can_call(
            run_id=run_id,
            estimated_input_tokens=estimated_input,
            estimated_output_tokens=max_output_tokens,
            checkpoint=checkpoint,
        )
        response: LLMResponse = self.wrapped.complete(
            prompt,
            model=model,
            max_output_tokens=max_output_tokens,
        )
        self._record(run_id=run_id, model=model, purpose=purpose, response=response)
        return response

    def _record(self, *, run_id: str, model: str, purpose: str, response: LLMResponse) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """insert into llm_usage
                (run_id, call_id, model, purpose, input_tokens, output_tokens, est_cost_usd, ts)
                values (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    str(uuid.uuid4()),
                    model,
                    purpose,
                    response.input_tokens,
                    response.output_tokens,
                    response.cost_estimate_usd,
                    datetime.now(UTC).isoformat(),
                ),
            )
            conn.commit()


def ensure_usage_table(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """create table if not exists llm_usage (
            run_id text not null,
            call_id text not null,
            model text not null,
            purpose text not null default '',
            input_tokens integer not null,
            output_tokens integer not null,
            est_cost_usd real not null,
            ts text not null,
            primary key (run_id, call_id)
        )"""
        )
        columns = {row[1] for row in conn.execute("pragma table_info(llm_usage)").fetchall()}
        if "purpose" not in columns:
            conn.execute("alter table llm_usage add column purpose text not null default ''")
        conn.commit()


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))
