from __future__ import annotations

import json
from pathlib import Path
from ragsentry.evalset.schema import EvalItem


def load_evalset(file_path: str | Path) -> list[EvalItem]:
    """Load evaluation items from a JSONL or JSON file."""
    
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Eval set file not found: {path}")


    items: list[EvalItem] = []

    if path.suffix.lower() == ".jsonl":
        with open(path, 'r', encoding="utf-8") as f:
            for line_idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)

                if "id" not in data:
                    data["id"] = f"q-{line_idx+1}"
                
                items.append(EvalItem(**data))

    elif path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            if not isinstance(raw_data, list):
                raise ValueError(f"Expected a JSON list of items in {path}")
            for idx, data in enumerate(raw_data):
                if "id" not in data:
                    data["id"] = f"q-{idx + 1}"
                items.append(EvalItem(**data))

    
    else: 
        raise ValueError(f"Unsupported file format '{path.suffix}'. Supported formats: .jsonl, .json")

    

    if not items:
           raise ValueError(f"Eval set {path} contains no valid evaluation items.")
    
    
    return items