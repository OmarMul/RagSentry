import json
import pytest
from ragsentry.evalset.loader import load_evalset


def test_load_jsonl_evalset(sample_evalset_file):
    evalset = load_evalset(str(sample_evalset_file))
    assert len(evalset) == 2
    assert evalset[0].id == "q1"
    assert evalset[0].question == "What is Python?"
    assert evalset[0].ground_truth == "Python is a programming language."
    assert evalset[1].id == "q2"


def test_load_json_array_evalset(tmp_path):
    json_path = tmp_path / "evalset.json"
    rows = [
        {"id": "q1", "question": "Question 1", "ground_truth": "Answer 1"},
    ]
    json_path.write_text(json.dumps(rows), encoding="utf-8")

    evalset = load_evalset(str(json_path))
    assert len(evalset) == 1
    assert evalset[0].id == "q1"


def test_load_nonexistent_evalset():
    with pytest.raises(FileNotFoundError):
        load_evalset("non_existent_file.jsonl")
