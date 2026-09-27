"""
RagSentry Adapter for the FAQ Bot fixture.

Scaffolded by following: skills/adapter-scaffolder/SKILL.md

The FAQ bot (faq_bot.ask) returns a non-standard shape:
    {"response": str, "sources": [{"text": str, "score": float, "category": str}]}

This adapter normalizes it to the RagSentry contract:
    {"answer": str, "contexts": list[str]}
"""
from __future__ import annotations

from typing import Any

from examples.faq_bot_fixture.faq_bot import ask


def query(question: str) -> dict[str, Any]:
    """RagSentry adapter: wraps the FAQ bot in the standard contract."""
    raw = ask(question)

    # The FAQ bot returns "response", not "answer"
    answer: str = raw["response"]

    # Sources are dicts with a "text" key — extract just the strings
    contexts: list[str] = [src["text"] for src in raw["sources"]]

    return {
        "answer": answer,
        "contexts": contexts,
        "metadata": {
            "total_searched": raw.get("total_searched", 0),
            "source_categories": [src["category"] for src in raw["sources"]],
        },
    }
