from __future__ import annotations

import json
from typing import Any
from pathlib import Path
from ragsentry.storage.base import RunResult, RunRow, RunStore


class LocalFileRunStore(RunStore):
    """Persists evaluation runs as JSON files in a local directory."""

    def __init__(self, output_dir: str | Path = "runs") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save(self, run: RunResult) -> str:
        # Create a file name based on timestamp and run_id
        safe_time = run.timestamp.replace(":", "-").replace(".", "-")
        file_path = self.output_dir / f"run_{safe_time}_{run.run_id}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(run.to_dict(), f, indent=2)

        return str(file_path)

    def load(self, run_id_or_path: str) -> RunResult:
        path = Path(run_id_or_path)
        if not path.exists():
            # Check inside output_dir directly
            candidate = self.output_dir / run_id_or_path
            if candidate.exists():
                path = candidate
            else:
                # Search for matching json files in output_dir
                matches = list(self.output_dir.glob(f"*{run_id_or_path}*.json"))
                if matches:
                    path = matches[0]
                else:
                    raise FileNotFoundError(f"Run file not found: {run_id_or_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        rows = [RunRow(**row) for row in data["rows"]]

        return RunResult(
            run_id=data["run_id"],
            timestamp=data["timestamp"],
            adapter=data["adapter"],
            evalset_path=data["evalset_path"],
            rows=rows,
            summary=data.get("summary", {}),
        )

    def list_runs(self) -> list[dict[str, Any]]:
        """List summary info for all stored runs."""
        runs = []
        for file_path in sorted(self.output_dir.glob("*.json"), reverse=True):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    runs.append({
                        "run_id": data.get("run_id"),
                        "timestamp": data.get("timestamp"),
                        "adapter": data.get("adapter"),
                        "evalset_path": data.get("evalset_path"),
                        "file_path": str(file_path),
                    })
            except Exception:
                continue
        return runs