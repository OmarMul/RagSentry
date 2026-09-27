import pytest
from ragsentry.diff import compare_runs


def test_compare_runs(sample_run_a, sample_run_b):
    diff = compare_runs(baseline=sample_run_a, candidate=sample_run_b)

    assert diff.baseline_run_id == "run_a"
    assert diff.candidate_run_id == "run_b"
    assert len(diff.rows) == 2

    # q1 should be unchanged
    q1_diff = next(q for q in diff.rows if q.id == "q1")
    assert q1_diff.status == "unchanged"

    # q2 should be regressed (faithfulness dropped from 0.8 to 0.6)
    q2_diff = next(q for q in diff.rows if q.id == "q2")
    assert q2_diff.status == "regressed"
    assert q2_diff.metric_deltas["faithfulness"].baseline == 0.8
    assert q2_diff.metric_deltas["faithfulness"].candidate == 0.6
    assert q2_diff.metric_deltas["faithfulness"].delta == -0.2
