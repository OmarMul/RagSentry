# RagSentry Adapter Contract

RagSentry interacts with target RAG applications strictly as black boxes through an **Adapter**. It supports three forms:

1. **Python Callable Adapter** (in-process)
2. **HTTP Adapter** (network API client)
3. **Shell Adapter** (subprocess stdin/stdout)

---

## 1. Python Callable Adapter

Wraps any Python function returning a dictionary containing `"answer"` (a string) and `"contexts"` (a list of strings).

### Requirements:
- Function signature: `query(question: str) -> dict[str, Any]`
- Required return keys:
  - `"answer"`: `str`
  - `"contexts"`: `list[str]` (retrieved text passages)
- Optional return key:
  - `"metadata"`: `dict` (traceability data, timestamps, etc.)

### Example CLI usage:
```powershell
ragsentry run -e evalset.jsonl -a my_package.retriever:query
```

---

## 2. HTTP Adapter

Points to any HTTP POST endpoint. Extracts answer and contexts using configurable JSONPath or dotted key paths.

### Requirements:
- Accepts a JSON payload: `{"question": "..."}`
- Returns a JSON response containing answer and contexts fields.

### Example CLI usage:
```powershell
ragsentry run -e evalset.jsonl -a http://localhost:8000/api/chat \
  --answer-path "data.reply" \
  --contexts-path "data.retrieved_sources"
```

---

## 3. Shell Adapter

Executes any binary, CLI script, or container, piping the question via `stdin` and reading JSON from `stdout`.

### Requirements:
- Receives the question string on standard input (`stdin`).
- Writes a JSON object to standard output (`stdout`) matching `{ "answer": "...", "contexts": ["..."] }`.

### Example CLI usage:
```powershell
ragsentry run -e evalset.jsonl -a "shell:python my_cli.py"
```
