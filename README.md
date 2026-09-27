# RagSentry — pytest for RAG

> **Regression testing and evaluation CLI for Retrieval-Augmented Generation (RAG) systems.**

RagSentry connects to your RAG application through a thin adapter, evaluates retrieved contexts and generated answers against your dataset, tracks runs over time, diffs runs to catch regressions, and gates CI builds.

---

## 🚀 Quickstart in 5 Minutes

### 1. Install RagSentry

```bash
pip install ragsentry
```

*(Optional PostgreSQL storage support: `pip install ragsentry[postgres]`)*

---

### 2. Initialize RagSentry in your project

```bash
ragsentry init
```

This scaffolds:
- `ragsentry_adapter.py` — starter adapter stub
- `evalset.jsonl` — starter evaluation set

---

### 3. Connect your RAG application

Edit `ragsentry_adapter.py` to call your RAG pipeline and return the required contract:

```python
from my_rag_app import ask_rag

def query(question: str) -> dict:
    result = ask_rag(question)
    return {
        "answer": result["answer"],
        "contexts": result["contexts"],  # list[str] of retrieved passages
    }
```

---

### 4. Run an Evaluation

#### Unscored Generation Pass (No LLM required):
```bash
ragsentry run -e evalset.jsonl -a ragsentry_adapter:query --no-scoring
```

#### Full Evaluation with LLM Judge:
```bash
ragsentry run -e evalset.jsonl -a ragsentry_adapter:query -p openrouter -m openai/gpt-oss-120b
```

---

### 5. Diff Runs & Gate CI

#### Diff two evaluation runs:
```bash
ragsentry diff run_2026-09-27T10-00-00_a1b2c3d4.json run_2026-09-27T11-00-00_e5f6g7h8.json
```

#### Quality Gate in CI (Exit code 0 on pass, non-zero on failure):
```bash
ragsentry ci \
  --candidate <candidate_run_id> \
  --baseline <baseline_run_id> \
  -t faithfulness=0.80 \
  -t context_recall=0.85 \
  --max-regressed-questions 1 \
  --pr-comment-out pr_comment.md
```

---

## ⚡ Key Features

- 🔌 **Plug-and-Play Adapters:** Supports Python callables (`pkg.mod:func`), REST APIs (`http://localhost:8000/query`), or CLI tools (`shell:python rag_cli.py`).
- 🤖 **Provider-Agnostic Judge Scoring:** Works with OpenAI, Anthropic, Gemini, Groq, xAI, Ollama, DeepSeek, OpenRouter, or custom OpenAI-compatible endpoints.
- 💾 **Dual Storage Backends:** Local JSON file store or PostgreSQL (`--storage postgresql://...`).
- 📊 **Rich Terminal Diffs:** Colorized diff tables highlighting improved, regressed, and unchanged questions per metric.
- 🚦 **CI Quality Gates:** Strict threshold enforcement and regression limits with exportable GitHub PR Markdown summaries.
- 🧩 **Agent-Usable Scaffolder Skill:** Includes `skills/adapter-scaffolder` so AI coding assistants can inspect unfamiliar RAG repos and scaffold adapters automatically.

---

## 📖 Documentation & Guides

- 📘 [Adapter Contract Guide](docs/adapter-contract.md)
- 📙 [CI / CD Integration Guide](docs/ci-integration.md)
- 📗 [Configuration Reference](docs/config-reference.md)
- 📕 [Adapter Scaffolder Skill](skills/adapter-scaffolder/SKILL.md)

---

## 📜 License

MIT License.