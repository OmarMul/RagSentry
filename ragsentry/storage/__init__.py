from __future__ import annotations

from ragsentry.storage.base import RunResult, RunRow, RunStore
from ragsentry.storage.local_file import LocalFileRunStore


def get_run_store(storage: str = "local", output_dir: str = "runs") -> RunStore:
    """Resolve RunStore based on storage URI ('local' or 'postgresql://...')."""
    storage_clean = storage.strip()
    if storage_clean.startswith("postgres://") or storage_clean.startswith("postgresql://"):
        from ragsentry.storage.postgres import PostgresRunStore
        return PostgresRunStore(dsn=storage_clean)
    return LocalFileRunStore(output_dir=output_dir)
