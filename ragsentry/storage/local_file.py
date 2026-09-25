from __future__ import annotations

import json
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
            # If not a direct path, check inside self.output_dir
            candidate = self.output_dir / run_id_or_path
            if candidate.exists():
                path = candidate
            
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