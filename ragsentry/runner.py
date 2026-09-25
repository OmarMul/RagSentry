from __future__ import annotations

import uuid
from datetime import datetime, timezone


from ragsentry.adapters.base import Adapter
from ragsentry.evalset.schema import EvalItem
from ragsentry.metrics.judge_config import JudgeConfig
from ragsentry.metrics.ragas_backend import score_run_rows
from ragsentry.storage.base import RunResult, RunRow

def run_eval(
    adapter: Adapter,
    evalset: list[EvalItem],
    adapter_name: str = "",
    evalset_path: str = "",
    judge_config: JudgeConfig | None = None,
) -> RunResult:
    """Run every item in the eval set through the adapter, score them with judge LLM."""

    run_id = uuid.uuid4().hex[:8]
    timestamp = datetime.now(timezone.utc).isoformat()
    rows: list[RunRow] = []


    for item in evalset:
        resp = adapter.query(item.question)
        row = RunRow(
            id=item.id,
            question=item.question,
            answer=resp.answer,
            contexts=resp.contexts,
            ground_truth=item.ground_truth,
            scores={},
            metadata={**item.metadata, **resp.metadata},
        )

        rows.append(row)
    
    summary: dict[str, object] = {"total_quetions": len(rows)}

    if judge_config:
        rows, avg_scores = score_run_rows(rows, judge_config)
        summary["judge_model"] = judge_config.model
        summary["average_scores"] = avg_scores


    return RunResult(
        run_id=run_id,
        timestamp=timestamp,
        adapter=adapter_name,
        evalset_path=evalset_path,
        rows=rows,
        summary=summary,
    )