from __future__ import annotations


from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class AdapterResponse:
    """Standardized response structure returned by any RagSentry adapter."""

    answer: str
    contexts: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


    def to_dict(self) -> dict[str, Any]:
        return{
            "answer": self.answer,
            "contexts": self.contexts,
            "metadata": self.metadata,
        }



@runtime_checkable
class Adapter(Protocol):
    """Protocol defining the adapter contract for external RAG systems."""

    def query(self, question: str) -> AdapterResponse:
        """Query the target RAG system with a question and return an AdapterResponse."""
        ...