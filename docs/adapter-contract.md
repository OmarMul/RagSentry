# Adapter Contract

RagSentry interacts with target RAG applications as black boxes through an **adapter**. Three adapter forms are supported:

1. [Python Callable Adapter](#1-python-callable-adapter)
2. [HTTP Adapter](#2-http-adapter)
3. [Shell Adapter](#3-shell-adapter)

All three forms must ultimately produce a response containing an `"answer"` string and a `"contexts"` list of strings. The form you choose depends on how your RAG application exposes its interface.

---

## 1. Python Callable Adapter

The Python callable adapter wraps any importable Python function. It is the simplest and most performant option.

### Requirements

- **Function signature:** `query(question: str) -> dict[str, Any]`
- **Required return keys:**
  - `"answer"` — `str`
  - `"contexts"` — `list[str]` (retrieved text passages)
- **Optional return key:**
  - `"metadata"` — `dict` (traceability data, timestamps, source IDs, etc.)

### Example

```python
# ragsentry_adapter.py
from my_package.retriever import ask

def query(question: str) -> dict:
    result = ask(question)
    return {
        "answer": result["response"],
        "contexts": [s.text for s in result["sources"]],
    }
```

### CLI usage

```bash
ragsentry run -e evalset.jsonl -a my_package.retriever:query
```

The `-a` / `--adapter` flag accepts a dotted module path followed by a colon and the callable name.

---

## 2. HTTP Adapter

The HTTP adapter sends a `POST` request to any endpoint and extracts the answer and contexts using configurable key paths.

### Requirements

- **Accepts:** a JSON payload `{"question": "..."}` as the request body
- **Returns:** a JSON response containing the answer and contexts fields at any nesting level

### Key path syntax

Use dotted key paths to address nested fields in the response JSON. For example, `data.reply` maps to `response["data"]["reply"]`.

### Example

```bash
ragsentry run -e evalset.jsonl \
  -a "http://localhost:8000/api/chat" \
  --answer-path "data.reply" \
  --contexts-path "data.retrieved_sources"
```

---

## 3. Shell Adapter

The shell adapter executes any binary, CLI script, or container, piping the question over `stdin` and reading JSON from `stdout`.

### Requirements

- **Input:** receives the question string on standard input (`stdin`)
- **Output:** writes a JSON object to standard output (`stdout`) matching `{"answer": "...", "contexts": ["..."]}`

### Example

```bash
ragsentry run -e evalset.jsonl -a "shell:python my_rag_cli.py"
```

The subprocess must flush `stdout` before exiting. Any output to `stderr` is captured separately and does not affect the adapter result.

---

## Choosing an Adapter Form

| Situation | Recommended Form |
| :--- | :--- |
| You can import the RAG function directly in Python | Python Callable |
| The RAG system runs as a separate service (FastAPI, Flask, REST) | HTTP |
| The RAG system is invoked as a command-line tool | Shell |

When in doubt, prefer the Python callable — it avoids serialization overhead and provides the richest error messages.
