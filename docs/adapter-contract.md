# RagSentry Adapter Contract

RagSentry interacts with target RAG applications strictly as black boxes through an **Adapter**. It supports three forms:

1. **Python Callable Adapter** (in-process)
2. **HTTP Adapter** (network API client)
3. **Shell Adapter** (subprocess stdin/stdout)

---

## 1. Python Callable Adapter
Wraps any Python function returning `{ "answer": str, "contexts": list[str], "metadata"?: dict }`.

```powershell
ragsentry run -e evals.jsonl -a my_package.retriever:query
```

## 1. HTTP Adapter
Points to any HTTP endpoint. Supports nested dotted paths (e.g. data.reply or result.sources) `{ "answer": str, "contexts": list[str], "metadata"?: dict }`.

```powershell
ragsentry run -e evals.jsonl -a http://localhost:8000/api/chat \
  --answer-path "data.reply" \
  --contexts-path "data.retrieved_sources"

```

## 1. Shell Adapter
Executes any binary, CLI script, or container, piping the question via stdin or CLI argument and reading JSON from stdout `{ "answer": str, "contexts": list[str], "metadata"?: dict }`.

```powershell
ragsentry run -e evals.jsonl -a "shell:python my_cli.py"
```
