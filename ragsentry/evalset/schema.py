from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class EvalItem(BaseModel):
    """A single evaluation question item."""
    id: str
    question: str
    ground_truth: str | None = None
    reference_contexts: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)