import pytest
from ragsentry.ci import evaluate_ci_gate
from ragsentry.storage.local_file import LocalFileRunStore


def test_ci_gate_pass(tmp_path, sample_run_a):
    store = LocalFileRunStore(output_dir=tmp_path)
    path_a = store.save(sample_run_a)

    # Threshold 0.7 vs actual 0.90 -> should pass
    res = evaluate_ci_gate(
        candidate=path_a,
        thresholds=["faithfulness=0.70"],
        storage=str(tmp_path),
    )
    assert res.passed is True
    assert len(res.violations) == 0


def test_ci_gate_fail_threshold(tmp_path, sample_run_a):
    store = LocalFileRunStore(output_dir=tmp_path)
    path_a = store.save(sample_run_a)

    # Threshold 0.95 vs actual 0.90 -> should fail
    res = evaluate_ci_gate(
        candidate=path_a,
        thresholds=["faithfulness=0.95"],
        storage=str(tmp_path),
    )
    assert res.passed is False
    assert len(res.violations) == 1
    assert "faithfulness" in res.violations[0]


def test_ci_gate_fail_regression(tmp_path, sample_run_a, sample_run_b):
    store = LocalFileRunStore(output_dir=tmp_path)
    path_a = store.save(sample_run_a)
    path_b = store.save(sample_run_b)

    # candidate=path_b, baseline=path_a, max_regressed_questions=0 -> q2 regressed, so should fail
    res = evaluate_ci_gate(
        candidate=path_b,
        baseline=path_a,
        max_regressed_questions=0,
        storage=str(tmp_path),
    )
    assert res.passed is False
    assert len(res.violations) == 1
    assert "Regression breach" in res.violations[0]
