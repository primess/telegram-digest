import sqlite3
from pathlib import Path

import pytest

from tg_digest.llm.accounting import AccountedLLM, BudgetEnforcer, BudgetExceeded, BudgetLimits
from tg_digest.testbed.fakes import FakeLLM
from tg_digest.types import Prompt


def test_accounted_llm_records_usage_to_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    enforcer = BudgetEnforcer(db_path, BudgetLimits(per_run_input_token_cap=1000))
    llm = AccountedLLM(FakeLLM(mode="echo"), db_path=db_path, budget=enforcer)

    response = llm.complete(
        Prompt(system="sys", user="hello world"),
        model="fake",
        max_output_tokens=20,
        run_id="run-1",
        purpose="test",
    )

    assert response.input_tokens > 0
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("select run_id, model, purpose from llm_usage").fetchall()
    assert rows == [("run-1", "fake", "test")]


def test_budget_enforcer_hard_stops_before_next_call_and_checkpoints(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    enforcer = BudgetEnforcer(db_path, BudgetLimits(per_run_input_token_cap=3))
    llm = AccountedLLM(FakeLLM(mode="echo"), db_path=db_path, budget=enforcer)

    with pytest.raises(BudgetExceeded) as exc_info:
        llm.complete(
            Prompt(system="sys", user="one two three four"),
            model="fake",
            max_output_tokens=20,
            run_id="run-2",
            purpose="summarise",
            checkpoint={"source_id": "verge", "last_processed_msg_id": 10},
        )

    assert exc_info.value.checkpoint == {"source_id": "verge", "last_processed_msg_id": 10}
    with sqlite3.connect(db_path) as conn:
        usage_count = conn.execute("select count(*) from llm_usage").fetchone()[0]
    assert usage_count == 0
