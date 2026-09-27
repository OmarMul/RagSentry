from __future__ import annotations

import json
from typing import Any


from ragsentry.storage.base import RunResult, RunRow, RunStore


class PostgresRunStore(RunStore):
    """Stores and loads evaluation runs from a PostgreSQL database."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        try:
            import psycopg
            from psycopg.rows import dict_row
            self._psycopg = psycopg
            self._dict_row = dict_row

        except ImportError:
            raise ImportError(
                "Postgres storage requires 'psycopg'. "
                "Install it with: pip install 'ragsentry[postgres]'"
            )
        
        self._init_db()

    
    def _get_connection(self):
        return self._psycopg.connect(self.dsn, row_factory=self._dict_row)


    
    def _init_db(self) -> None:
        """Create the runs table if it does not already exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS ragsentry_runs (
            run_id VARCHAR(64) PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL,
            adapter VARCHAR(255) NOT NULL,
            evalset_path VARCHAR(512),
            data JSONB NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_ragsentry_runs_timestamp ON ragsentry_runs(timestamp DESC);
        """


        with self._get_connection() as conn:

            with conn.cursor() as cur:
                cur.execute(create_table_sql)
            
            conn.commit()

        
    def save(self, run: RunResult) -> str:
        """Persist a RunResult to the PostgreSQL database."""
        insert_sql = """
        INSERT INTO ragsentry_runs (run_id, timestamp, adapter, evalset_path, data)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (run_id) DO UPDATE SET
            timestamp = EXCLUDED.timestamp,
            adapter = EXCLUDED.adapter,
            evalset_path = EXCLUDED.evalset_path,
            data = EXCLUDED.data;
        """

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    insert_sql,
                    (
                        run.run_id,
                        run.timestamp,
                        run.adapter,
                        run.evalset_path,
                        json.dumps(run.to_dict()),
                    ),
                )
            conn.commit()
        return f"postgres://{run.run_id}"

    
    def load(self, run_id_or_path: str) -> RunResult:
        """Load a RunResult by its run_id."""
        clean_id = run_id_or_path
        if clean_id.startswith("postgres://"):
            clean_id = clean_id.replace("postgres://", "").strip()
        

        select_sql = "SELECT data FROM ragsentry_runs WHERE run_id = %s;"

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(select_sql, (clean_id,))
                row = cur.fetchone()

        
        if not row:
            raise FileNotFoundError(f"Run '{run_id_or_path}' not found in PostgreSQL.")
        

        data = row["data"]
        if isinstance(data, str):
            data = json.loads(data)

        
        rows = [RunRow(**r) for r in data["rows"]]


        return RunResult(
            run_id=data["run_id"],
            timestamp=data["timestamp"],
            adapter=data["adapter"],
            evalset_path=data["evalset_path"],
            rows=rows,
            summary=data.get("summary", {}),
        )