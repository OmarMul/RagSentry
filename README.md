# RagSentry

**Regression testing and evaluation CLI for Retrieval-Augmented Generation (RAG) systems.**

RagSentry connects to your RAG application through a thin adapter, evaluates retrieved contexts and generated answers against a dataset, tracks runs over time, diffs runs to catch regressions, and gates CI builds.

---

## Table of Contents

- [Installation](#installation)
- [Quickstart](#quickstart)
- [Key Features](#key-features)
- [Agent Skill: Adapter Scaffolder](#agent-skill-adapter-scaffolder)
- [Documentation](#documentation)
- [License](#license)

---

## Installation

```bash
pip install ragsentry
```

Optional PostgreSQL storage support:

```bash
pip install "ragsentry[postgres]"
```

---

## Quickstart

### 1. Initialize the project

```bash
ragsentry init
```

This scaffolds two files in the current directory:

- `ragsentry_adapter.py` — a starter adapter stub
- `evalset.jsonl` — a starter evaluation dataset

### 2. Connect your RAG application

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

See the [Adapter Contract Guide](docs/adapter-contract.md) for all supported adapter forms (Python callable, HTTP endpoint, shell subprocess).

### 3. Run an evaluation

Unscored generation pass (no LLM required):

```bash
ragsentry run -e evalset.jsonl -a ragsentry_adapter:query --no-scoring
```

Full evaluation with an LLM judge:

```bash
ragsentry run -e evalset.jsonl -a ragsentry_adapter:query -p openrouter -m openai/gpt-4o
```

### 4. Diff runs and gate CI

Diff two evaluation runs:

```bash
ragsentry diff run_2026-09-27T10-00-00_a1b2c3d4.json run_2026-09-27T11-00-00_e5f6g7h8.json
```

Quality gate in CI (exit code `0` on pass, non-zero on failure):

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

## Key Features

- **Plug-and-Play Adapters.** Supports Python callables (`pkg.mod:func`), REST APIs (`http://localhost:8000/query`), and CLI tools (`shell:python rag_cli.py`).
- **Provider-Agnostic Judge Scoring.** Works with OpenAI, Anthropic, Gemini, Groq, xAI, Ollama, DeepSeek, OpenRouter, or any custom OpenAI-compatible endpoint.
- **Dual Storage Backends.** Local JSON file store or PostgreSQL (`--storage postgresql://...`).
- **Rich Terminal Diffs.** Colorized diff tables highlighting improved, regressed, and unchanged questions per metric.
- **CI Quality Gates.** Strict threshold enforcement and regression limits with exportable GitHub PR Markdown summaries.
- **Agent-Usable Scaffolder Skill.** Includes `skills/adapter-scaffolder` so AI coding assistants can inspect unfamiliar RAG repositories and scaffold adapters automatically.

---

## Agent Skill: Adapter Scaffolder

RagSentry ships a skill file (`skills/adapter-scaffolder/SKILL.md`) that AI coding assistants can read to automatically inspect an unfamiliar RAG codebase and generate a working `ragsentry_adapter.py`.

Install the skill into your agent's configuration with a single command:

```bash
# Install to local workspace (.agents/skills/adapter-scaffolder)
ragsentry install-skill

# Install for a specific agent
ragsentry install-skill --agent claude
ragsentry install-skill --agent cursor
ragsentry install-skill --agent windsurf

# Global install (available across all workspaces)
ragsentry install-skill --global
```

See the [Agent Skill Installation Guide](docs/agent-skill-installation.md) for full details.

---

## Documentation

| Guide | Description |
| :--- | :--- |
| [Adapter Contract](docs/adapter-contract.md) | Supported adapter forms and their required contracts |
| [CI/CD Integration](docs/ci-integration.md) | GitHub Actions, GitLab CI, and generic pipeline setup |
| [Configuration Reference](docs/config-reference.md) | Judge providers, storage backends, and all CLI options |
| [Agent Skill Installation](docs/agent-skill-installation.md) | Installing the adapter scaffolder skill for AI agents |
| [Adapter Scaffolder Skill](skills/adapter-scaffolder/SKILL.md) | The skill specification read by AI coding assistants |

---

## License

MIT. See [LICENSE](LICENSE) for details.