from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


from ragsentry.storage.base import RunResult, RunRow
from ragsentry.storage.local_file import LocalFileRunStore


@dataclass
class MetricDelta:
    """Represents the change in a single metric score."""
    metric: str
    baseline: float | None
    candidate: float | None
    delta: float | None
    status: str  # "improved", "regressed", "unchanged", "n/a"



@dataclass
class RowDiff:
    """Represents the diff of an individual question between two runs."""
    id: str
    question: str
    status: str  # "improved", "regressed", "unchanged", "new", "removed"
    metric_deltas: dict[str, MetricDelta] = field(default_factory=dict)
    answer_changed: bool = False
    contexts_changed: bool = False



@dataclass
class RunDiff:
    """Complete diff report between a baseline run and candidate run."""
    baseline_run_id: str
    candidate_run_id: str
    baseline_timestamp: str
    candidate_timestamp: str
    rows: list[RowDiff] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compare_runs(
    baseline: RunResult | str | Path,
    candidate: RunResult | str | Path,
    tolerance: float = 0.001,
) -> RunDiff:
    """Compare two evaluation runs and compute score deltas per question and metric."""


    store = LocalFileRunStore()

    if isinstance(baseline, (str, Path)):
        baseline = store.load(str(baseline))

    if isinstance(candidate, (str, Path)):
        candidate = store.load(str(candidate))


    
    base_rows: dict[str, RunRow] = {r.id: r for r in baseline.rows}
    cand_rows: dict[str, RunRow] = {r.id: r for r in candidate.rows}

    all_ids = list(dict.fromkeys(list(base_rows.keys()) + list(cand_rows.keys())))
    row_diffs: list[RowDiff] = []
    

    counts = {
        "improved": 0,
        "regressed": 0,
        "unchanged": 0,
        "new": 0,
        "removed": 0,
    }


    all_metrics: set[str] = set()


    for q_id in all_ids:
        b_row = base_rows.get(q_id)
        c_row = cand_rows.get(q_id)

        if b_row is None and c_row is not None:
            # Question added in candidate
            counts["new"] += 1
            row_diffs.append(
                RowDiff(
                    id=q_id,
                    question=c_row.question,
                    status="new",
                    answer_changed=True,
                    contexts_changed=True,
                )
            )
            continue


        if c_row is None and b_row is not None:
            # Question removed in candidate
            counts["removed"] += 1
            row_diffs.append(
                RowDiff(
                    id=q_id,
                    question=b_row.question,
                    status="removed",
                    answer_changed=True,
                    contexts_changed=True,
                )
            )
            continue


        assert b_row is not None and c_row is not None


        #compare matrics
        metric_keys = set(b_row.scores.keys()) | set(c_row.scores.keys())
        all_metrics.update(metric_keys)
        m_deltas: dict[str, MetricDelta] ={}

        has_regressed = False
        has_improved = False

        for m_name in metric_keys:
            b_val = b_row.scores.get(m_name)
            c_val = c_row.scores.get(m_name)


            if b_val is not None and c_val is not None:
                delta = round(c_val - b_val, 4)
                if delta < -tolerance:
                    m_status = "regressed"
                    has_regressed = True
                
                elif delta > tolerance:
                    m_status = "improved"
                    has_improved = True

                else:
                    m_status = "unchanged"

            else:
                delta = None
                m_status = "n/a"

            
            m_deltas[m_name] = MetricDelta(
                metric=m_name,
                baseline=b_val,
                candidate=c_val,
                delta=delta,
                status=m_status,
            )

        #overall row status

        if has_regressed:
            row_status = "regressed"
            counts["regressed"] += 1
        elif has_improved:
            row_status = "improved"
            counts["improved"] += 1
        else:
            row_status = "unchanged"
            counts["unchanged"] += 1

        row_diffs.append(
            RowDiff(
                id=q_id,
                question=c_row.question,
                status=row_status,
                metric_deltas=m_deltas,
                answer_changed=(b_row.answer != c_row.answer),
                contexts_changed=(b_row.contexts != c_row.contexts),
            )
        )

    # Calculate average metric deltas
    base_summary = baseline.summary.get("average_scores", {})
    cand_summary = candidate.summary.get("average_scores", {})
    average_deltas: dict[str, dict[str, Any]] = {}

    
    for m in all_metrics:
        b_avg = base_summary.get(m)
        c_avg = cand_summary.get(m)
        d_avg = round(c_avg - b_avg, 4) if (b_avg is not None and c_avg is not None) else None
        average_deltas[m] = {
            "baseline": b_avg,
            "candidate": c_avg,
            "delta": d_avg,
        }
    summary = {
        "total_questions": len(all_ids),
        "counts": counts,
        "average_deltas": average_deltas,
    }
    return RunDiff(
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        baseline_timestamp=baseline.timestamp,
        candidate_timestamp=candidate.timestamp,
        rows=row_diffs,
        summary=summary,
    )
