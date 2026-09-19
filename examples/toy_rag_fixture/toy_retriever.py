"""
Minimal keyword-based RAG fixture.
NOTE: This is for testing/fixtures only and is NOT part of the core product.
"""

from typing import Any

DOCUMENTS = [
    {
        "id": "doc-1",
        "text": "RagSentry is a regression testing and evaluation tool for RAG systems.",
    },
    {
        "id": "doc-2",
        "text": "RagSentry uses adapters to treat external RAG systems as black boxes.",
    },
    {
        "id": "doc-3",
        "text": "RagSentry scores answers using swappable judge models with RAGAS metrics.",
    },
]


def query(question: str) -> dict[str, Any]:
    """Simple keyword matching retriever and answer synthesizer."""
    q_words = set(question.lower().split())
    matched_contexts: list[str] = []

    for doc in DOCUMENTS:
        doc_words = set(doc["text"].lower().split())
        if q_words & doc_words:
            matched_contexts.append(doc["text"])

    if matched_contexts:
        answer = "Based on retrieved context: " + " ".join(matched_contexts)
    else:
        answer = "I do not have enough information to answer that question."

    return {
        "answer": answer,
        "contexts": matched_contexts,
        "metadata": {"matched_count": len(matched_contexts)},
    }
