import json
import pytest
from pathlib import Path
from ragsentry.storage.base import RunResult, RunRow


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def sample_evalset_file(tmp_path: Path) -> Path:
    evalset_path = tmp_path / "test_evalset.jsonl"
    rows = [
        {"id": "q1", "question": "What is Python?", "ground_truth": "Python is a programming language."},
        {"id": "q2", "question": "What is RagSentry?", "ground_truth": "RagSentry is a RAG evaluation CLI tool."},
    ]
    with open(evalset_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return evalset_path


@pytest.fixture
def sample_run_a() -> RunResult:
    return RunResult(
        run_id="run_a",
        timestamp="2026-09-27T10:00:00Z",
        adapter="test_adapter:query",
        evalset_path="test_evalset.jsonl",
        rows=[
            RunRow(
                id="q1",
                question="What is Python?",
                answer="Python is a programming language.",
                contexts=["Python is a language."],
                scores={"faithfulness": 1.0, "context_recall": 1.0},
            ),
            RunRow(
                id="q2",
                question="What is RagSentry?",
                answer="RagSentry is a CLI tool.",
                contexts=["RagSentry is a tool for RAG testing."],
                scores={"faithfulness": 0.8, "context_recall": 0.9},
            ),
        ],
        summary={
            "average_scores": {"faithfulness": 0.9, "context_recall": 0.95},
        },
    )


@pytest.fixture
def sample_run_b() -> RunResult:
    return RunResult(
        run_id="run_b",
        timestamp="2026-09-27T11:00:00Z",
        adapter="test_adapter:query",
        evalset_path="test_evalset.jsonl",
        rows=[
            RunRow(
                id="q1",
                question="What is Python?",
                answer="Python is a language.",
                contexts=["Python is a language."],
                scores={"faithfulness": 1.0, "context_recall": 1.0},
            ),
            RunRow(
                id="q2",
                question="What is RagSentry?",
                answer="RagSentry does testing.",
                contexts=["RagSentry does testing."],
                scores={"faithfulness": 0.6, "context_recall": 0.7},  # Regressed
            ),
        ],
        summary={
            "average_scores": {"faithfulness": 0.8, "context_recall": 0.85},
        },
    )
