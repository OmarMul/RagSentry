---
name: adapter-scaffolder
description: >
  Step-by-step procedure for an AI coding assistant to inspect an unfamiliar RAG
  codebase, locate the retrieval call site, and scaffold a working RagSentry
  adapter file. Works for Python callable, HTTP endpoint, and shell/subprocess
  adapter forms.
---

# Adapter Scaffolder Skill

## Purpose

You are helping a developer connect their existing RAG application to RagSentry
for evaluation and regression testing. Your job is to:

1. **Inspect** the target codebase to find where retrieval and answer generation
   happen.
2. **Identify** the function signature, return shape, and how `answer` and
   `contexts` (retrieved passages) are produced.
3. **Scaffold** a working adapter file that conforms to the RagSentry adapter
   contract.

The adapter contract requires a function with this signature:

```python
def query(question: str) -> dict[str, Any]:
    """Must return {"answer": str, "contexts": list[str], ...}"""
```

## Prerequisites

- The user has RagSentry installed (`pip install ragsentry`)
- The user has a RAG application they want to evaluate
- You have access to the target codebase's source files

---

## Procedure

### Phase 1 — Discover the Retrieval Entry Point

**Goal:** Find the function or endpoint that takes a user question and returns
an answer with retrieved contexts.

1. **Ask the user** (if not already clear):
   - "Where is your RAG application's code? Which directory or module?"
   - "How do users normally query it? (Python function call, HTTP API, CLI command)"

2. **Search for retrieval patterns.** Look for common indicators:
   ```
   retrieve
   search
   query
   rag
   context
   vector
   embedding
   similarity
   chunk
   document
   ```

3. **Trace the data flow.** Starting from the entry point, identify:
   - **Input:** How does the question string arrive? (function parameter, HTTP
     request body, stdin)
   - **Retrieval:** Where are documents/passages fetched? (vector DB call,
     keyword search, API call)
   - **Generation:** Where is the answer synthesized? (LLM call, template,
     concatenation)
   - **Output:** What is the return type? (dict, dataclass, Pydantic model,
     HTTP response)

4. **Document your findings** before writing any code:
   - Module path: `myapp.rag_pipeline`
   - Function name: `ask` (or endpoint: `POST /api/query`)
   - Input: `question: str`
   - Return type: `dict` with keys `{"response", "sources", "metadata"}`
   - Answer location: `result["response"]`
   - Contexts location: `result["sources"]` — each source has a `.text` field

### Phase 2 — Choose the Adapter Form

Based on what you discovered in Phase 1, pick the right adapter form:

| Situation | Adapter Form | Template |
| :--- | :--- | :--- |
| You can import the RAG function directly in Python | Python Callable | `templates/python_adapter.py` |
| The RAG system is behind an HTTP API | HTTP Endpoint | `templates/http_adapter.py` |
| The RAG system is a CLI tool or subprocess | Shell | `templates/shell_adapter.py` |

**Decision guide:**
- Prefer **Python Callable** when possible — it is the fastest and simplest.
- Use **HTTP** when the RAG app runs as a separate service (e.g., FastAPI,
  Flask, or any REST API).
- Use **Shell** when the RAG app is invoked as a command-line tool.

### Phase 3 — Scaffold the Adapter

1. **Copy the appropriate template** from `skills/adapter-scaffolder/templates/`
   into the user's project root (or wherever they prefer).

2. **Fill in the placeholders** based on Phase 1 findings:

#### Python Callable Adapter

```python
# ragsentry_adapter.py
from myapp.rag_pipeline import ask  # real import

def query(question: str) -> dict[str, Any]:
    result = ask(question)  # real function call
    return {
        "answer": result["response"],               # real answer key
        "contexts": [s.text for s in result["sources"]],  # real contexts
    }
```

Then test with:
```bash
ragsentry run -e evalset.jsonl -a ragsentry_adapter:query
```

#### HTTP Adapter

```bash
# No adapter file needed — use the built-in HTTP adapter:
ragsentry run -e evalset.jsonl \
  -a "http://localhost:8000/api/query" \
  --adapter-type http \
  --answer-path "response" \
  --contexts-path "sources"
```

If the response shape is complex (e.g., contexts are nested objects), create a
thin wrapper adapter using `templates/http_adapter.py`.

#### Shell Adapter

```bash
# No adapter file needed — use the built-in shell adapter:
ragsentry run -e evalset.jsonl \
  -a "shell:python my_rag_cli.py" \
  --adapter-type shell
```

The shell command receives the question on stdin and must print JSON
`{"answer": "...", "contexts": [...]}` to stdout.

### Phase 4 — Verify

1. **Run a smoke test** with a single question to confirm the adapter works:
   ```bash
   python -c "from ragsentry_adapter import query; print(query('test question'))"
   ```

2. **Check the contract** — the output must be a dict with:
   - `"answer"`: a string
   - `"contexts"`: a list of strings (the retrieved passages)

3. **Run a full evaluation** against the user's eval set:
   ```bash
   ragsentry run -e evalset.jsonl -a ragsentry_adapter:query
   ```

4. If the run produces a scored result file under `runs/`, the adapter is
   working correctly.

---

## Common Pitfalls

| Problem | Fix |
| :--- | :--- |
| Contexts are objects, not strings | Map them: `[c.page_content for c in raw_contexts]` or `[c["text"] for c in raw_contexts]` |
| Function returns a Pydantic model | Call `.model_dump()` or access attributes directly |
| RAG function is async | Wrap with `asyncio.run()` in the adapter |
| RAG function requires session/config | Initialize in module scope, outside `query()` |
| Import fails due to missing env vars | Set them before import, or use a try/except with a helpful error message |

---

## Validation Checklist

Before declaring the adapter complete, verify:

- [ ] `query("any question")` returns `{"answer": str, "contexts": list[str]}`
- [ ] Contexts are **strings** (not dicts, not objects)
- [ ] The function is importable via dotted path (e.g., `ragsentry_adapter:query`)
- [ ] `ragsentry run -e evalset.jsonl -a <dotted_path>:query` completes without errors
- [ ] The generated `runs/*.json` file contains scores for all questions

