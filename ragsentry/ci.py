from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


from ragsentry.diff import RunDiff, compare_runs
from ragsentry.storage.base import RunResult
from ragsentry.storage import get_run_store



@dataclass
class CIGateResult:
    """Outcome of a CI quality gate check."""
    passed: bool
    violations: list[str] = field(default_factory=list)
    candidate_run: RunResult | None = None
    baseline_run: RunResult | None = None
    diff: RunDiff | None = None
    thresholds: dict[str, float] = field(default_factory=dict)
    max_regression: float | None = None
    max_regressed_questions: int = 0


    @property
    def exit_code(self) -> int:
        return 0 if self.passed else 1

def parse_thresholds(threshold_inputs: list[str] | dict[str, float] | None) -> dict[str, float]:
    """Parse threshold inputs from list of 'metric=val' strings or dict."""
    if not threshold_inputs:
        return {}

    if isinstance(threshold_inputs, dict):
        return {k: float(v) for k, v in threshold_inputs.items()}


    result: dict[str, float] = {}
    for item in threshold_inputs:
        item = item.strip()
        if not item:
            continue
        if "=" in item:
            k, v = item.split("=", 1)
            result[k.strip()] = float(v.strip())

        elif ":" in item:
            k, v = item.split(":", 1)
            result[k.strip()] = float(v.strip())

    
    return result



def evaluate_ci_gate(
    candidate: RunResult | str | Path,
    baseline: RunResult | str | Path | None = None,
    thresholds: dict[str, float] | list[str] | None = None,
    max_regression: float | None = None,
    max_regressed_questions: int = 0,
    tolerance: float = 0.001,
    storage: str = "local",
) -> CIGateResult:
    """
    Check if a candidate run satisfies CI quality criteria:
    1. Absolute thresholds (e.g. faithfulness >= 0.8)
    2. Regression checks against baseline (e.g. max drop <= 0.05, max regressed questions <= 0)
    """

    store = get_run_store(storage=storage)
    violations: list[str] = []

    if isinstance(candidate, (str, Path)):
        cand_run = store.load(str(candidate))

    else:
        cand_run = candidate

    
    base_run: RunResult | None = None
    diff: RunDiff | None = None

    if baseline:
        if isinstance(baseline, (str, Path)):
            base_run = store.load(str(baseline))

        else:
            base_run = baseline
        
        diff = compare_runs(base_run, cand_run, tolerance=tolerance)


    
    parsed_thresh = parse_thresholds(thresholds)
    avg_scores = cand_run.summary.get("average_scores", {})


    # 1. Absolute Threshold Checks
    for metric, min_val in parsed_thresh.items():
        actual_val = avg_scores.get(metric)
        if actual_val is None:
            violations.append(
                f"Missing metric '{metric}': expected >= {min_val:.4f}, but metric was not scored."
            )
        elif actual_val < min_val:
            violations.append(
                f"Threshold breach on '{metric}': score {actual_val:.4f} < required minimum {min_val:.4f}."
            )

    # 2. Baseline Regression Checks
    if diff:
        counts = diff.summary.get("counts", {})
        regressed_q_count = counts.get("regressed", 0)


        if regressed_q_count > max_regressed_questions:
            violations.append(
                f"Regression breach: {regressed_q_count} questions regressed (max allowed: {max_regressed_questions})."
            )

        

        if max_regression is not None:
            avg_deltas = diff.summary.get("average_deltas", {})
            for m_name, d_info in avg_deltas.items():
                delta = d_info.get("delta")
                if delta is not None and delta < -max_regression:
                    violations.append(
                        f"Regression breach on '{m_name}': average score dropped by {abs(delta):.4f} "
                        f"(max allowed drop: {max_regression:.4f})."
                    )
    passed = len(violations) == 0


    return CIGateResult(
        passed=passed,
        violations=violations,
        candidate_run=cand_run,
        baseline_run=base_run,
        diff=diff,
        thresholds=parsed_thresh,
        max_regression=max_regression,
        max_regressed_questions=max_regressed_questions,
    )

    