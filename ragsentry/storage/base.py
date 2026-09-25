from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol, runtime_checkable



@dataclass
class RunRow:
    """Represents a single evaluated row in a run."""
    id: str
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str | None = None
    scores: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)



@dataclass
class RunResult:
    """Represents the complete result of an evaluation run."""
    run_id: str
    timestamp: str
    adapter: str
    evalset_path: str
    rows: list[RunRow]
    summary: dict[str, Any] = field(default_factory=dict)


    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@runtime_checkable
class RunStore(Protocol):
    """Protocol for storing and retrieving evaluation runs."""
    def save(self, run: RunResult) -> str:
        """Persist a RunResult and return the destination identifier or path."""
        ...
    def load(self, run_id_or_path: str) -> RunResult:
        """Load a RunResult by ID or file path."""
        ...