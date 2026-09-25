from __future__ import annotations

from typing import Any
import httpx


from ragsentry.adapters.base import Adapter, AdapterResponse


def extract_path(data: Any, path: str) -> Any:
    """Extract a nested value using dotted syntax like 'data.answer' or 'results.0.text'."""
    if not path:
        return data

    current = data
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)

        elif isinstance(current, (list, tuple)) and part.isdigit():
            idx = int(part)
            current = current[idx] if 0<= idx < len(current) else None

        else:
            return None
        
        if current is None:
            break
    return current




class HttpAdapter(Adapter):
    """Adapter that queries an external RAG service over HTTP."""

    def __init__(
        self, 
        url: str,
        method: str = "POST",
        headers: dict[str, str] | None = None,
        question_key: str = "question",
        answer_path: str = "answer",
        contexts_path: str = "contexts",
        metadata_path: str | None = "metadata",
        timeout: float =30.0
    ) -> None:
        self.url = url
        self.method = method.upper()
        self.headers = headers or {"Content-Type": "application/json"}
        self.question_key = question_key
        self.answer_path = answer_path
        self.contexts_path = contexts_path
        self.metadata_path = metadata_path
        self.timeout = timeout


    def query(self, question: str) -> AdapterResponse:
        payload = {self.question_key: question}

        with httpx.Client(timeout=self.timeout) as client:
            if self.method == "POST":
                response = client.post(self.url ,json=payload, headers=self.headers)
            elif self.method == "GET":
                response = client.get(self.url ,params=payload, headers=self.headers)

            else:
                raise ValueError(f"Unsupported HTTP method: {self.method}")

            
            response.raise_for_status()
            data = response.json()

        
        #extract the answer
        raw_answer = extract_path(data, self.answer_path)
        if raw_answer is None:
            raise ValueError(
                f"Failed to extract answer using path '{self.answer_path}' from response: {data}"
            )

        #extract the contexts
        raw_contexts = extract_path(data, self.contexts_path)
        if raw_contexts is None:
            raw_contexts = []
        elif not isinstance(raw_contexts, list):
            raw_contexts = [raw_contexts]

        contexts = [
            c if isinstance(c, str) else str(c.get("text", c)) if isinstance(c, dict) else str(c)
            for c in raw_contexts
        ]

        #extract metadata
        metadata = {}
        if self.metadata_path:
            raw_meta = extract_path(data, self.metadata_path)
            if isinstance(raw_meta, dict):
                metadata = raw_meta

        
        return AdapterResponse(
            answer=str(raw_answer),
            contexts=contexts,
            metadata=metadata
        )