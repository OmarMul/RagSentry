"""
FAQ Bot — a second RAG fixture for testing RagSentry's adapter scaffolder.

NOTE: This is for testing/fixtures only and is NOT part of the core product.

Unlike toy_rag_fixture, this fixture:
  - Uses FAQ entries with q/a/category fields (not flat documents)
  - Computes TF-IDF-style relevance scores instead of keyword intersection
  - Returns a non-standard response shape: {"response": str, "sources": [...]}
  - Sources are dicts with {"text", "score", "category"} — not plain strings
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Any


FAQ_ENTRIES = [
    {
        "q": "How do I install RagSentry?",
        "a": "Install with pip: pip install ragsentry",
        "category": "setup",
    },
    {
        "q": "What metrics does RagSentry use?",
        "a": "RagSentry uses RAGAS metrics: faithfulness, answer relevancy, context precision, and context recall.",
        "category": "metrics",
    },
    {
        "q": "How do I create an adapter?",
        "a": "Create a Python function with signature query(question: str) -> dict that returns answer and contexts.",
        "category": "adapters",
    },
    {
        "q": "Can RagSentry store results in PostgreSQL?",
        "a": "Yes, install ragsentry[postgres] and pass --storage postgresql://... to the CLI.",
        "category": "storage",
    },
    {
        "q": "How does the CI gate work?",
        "a": "The CI gate checks absolute thresholds and regression against a baseline run, exiting with code 1 on failure.",
        "category": "ci",
    },
]


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + lowercase tokenizer."""
    return [w.strip("?.,!:;\"'()") for w in text.lower().split() if w.strip("?.,!:;\"'()")]


def _tf_idf_score(query_tokens: list[str], doc_text: str) -> float:
    """Simplified TF-IDF-ish relevance score."""
    doc_tokens = _tokenize(doc_text)
    if not doc_tokens:
        return 0.0

    doc_freq = Counter(doc_tokens)
    score = 0.0
    for qt in query_tokens:
        tf = doc_freq.get(qt, 0) / len(doc_tokens)
        # Simplified IDF: log(total_entries / (1 + docs containing term))
        docs_with_term = sum(1 for faq in FAQ_ENTRIES if qt in _tokenize(faq["a"] + " " + faq["q"]))
        idf = math.log((len(FAQ_ENTRIES) + 1) / (1 + docs_with_term))
        score += tf * idf

    return round(score, 4)


def ask(question: str) -> dict[str, Any]:
    """
    FAQ Bot retrieval: scores all FAQ entries against the question using
    TF-IDF and returns the top matches.

    Returns a NON-STANDARD shape:
        {
            "response": str,
            "sources": [{"text": str, "score": float, "category": str}, ...],
            "total_searched": int,
        }

    An adapter scaffolded by the skill must normalize this to:
        {"answer": str, "contexts": list[str]}
    """
    query_tokens = _tokenize(question)

    scored: list[tuple[float, dict[str, Any]]] = []
    for faq in FAQ_ENTRIES:
        combined_text = faq["q"] + " " + faq["a"]
        score = _tf_idf_score(query_tokens, combined_text)
        if score > 0:
            scored.append((score, faq))

    # Sort by relevance score descending, take top 3
    scored.sort(key=lambda x: x[0], reverse=True)
    top_matches = scored[:3]

    if top_matches:
        best = top_matches[0][1]
        response_text = best["a"]
    else:
        response_text = "I don't have an answer for that question in my FAQ database."

    sources = [
        {
            "text": faq["a"],
            "score": sc,
            "category": faq["category"],
        }
        for sc, faq in top_matches
    ]

    return {
        "response": response_text,
        "sources": sources,
        "total_searched": len(FAQ_ENTRIES),
    }


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    result = ask("How do I install RagSentry?")
    print(f"Response: {result['response']}")
    print(f"Sources:  {len(result['sources'])} matched")
    for src in result["sources"]:
        print(f"  [{src['category']}] (score={src['score']}) {src['text']}")
