from pathlib import Path
import pytest
from ragsentry.storage.local_file import LocalFileRunStore
from ragsentry.storage.base import RunResult, RunRow


def test_local_file_run_store_save_and_load(tmp_path, sample_run_a):
    store = LocalFileRunStore(output_dir=tmp_path)

    path_str = store.save(sample_run_a)
    assert Path(path_str).exists()

    loaded_run = store.load(sample_run_a.run_id)
    assert loaded_run.run_id == sample_run_a.run_id
    assert loaded_run.adapter == sample_run_a.adapter
    assert len(loaded_run.rows) == len(sample_run_a.rows)
    assert loaded_run.rows[0].id == "q1"


def test_local_file_run_store_list(tmp_path, sample_run_a, sample_run_b):
    store = LocalFileRunStore(output_dir=tmp_path)
    store.save(sample_run_a)
    store.save(sample_run_b)

    runs = store.list_runs()
    assert len(runs) == 2
    run_ids = [r["run_id"] for r in runs]
    assert "run_a" in run_ids
    assert "run_b" in run_ids


def test_local_file_run_store_not_found(tmp_path):
    store = LocalFileRunStore(output_dir=tmp_path)
    with pytest.raises(FileNotFoundError):
        store.load("non_existent_run_id")
