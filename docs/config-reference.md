# Configuration Reference

RagSentry is configured primarily through CLI flags. This reference documents all configurable subsystems: judge model providers, storage backends, and CI gate options.

---

## Table of Contents

- [Judge Model Providers](#judge-model-providers)
- [Storage Backends](#storage-backends)
- [CI Gate Options](#ci-gate-options)

---

## Judge Model Providers

RagSentry scores RAG answers using a swappable judge LLM via RAGAS. Switch between providers with a single CLI flag (`-p` / `--judge-provider`) or through a JSON config file.

### Provider Selection

```bash
# OpenAI (default model: gpt-4o-mini)
ragsentry run -e evalset.jsonl -a app.rag:query -p openai

# Anthropic Claude (default model: claude-3-5-haiku-latest)
ragsentry run -e evalset.jsonl -a app.rag:query -p anthropic

# Google Gemini (default model: gemini-1.5-flash)
ragsentry run -e evalset.jsonl -a app.rag:query -p gemini

# Groq (default model: llama-3.1-8b-instant)
ragsentry run -e evalset.jsonl -a app.rag:query -p groq

# xAI Grok (default model: grok-2-latest)
ragsentry run -e evalset.jsonl -a app.rag:query -p xai

# Local Ollama (default model: llama3.2 on localhost:11434)
ragsentry run -e evalset.jsonl -a app.rag:query -p ollama

# DeepSeek (default model: deepseek-chat)
ragsentry run -e evalset.jsonl -a app.rag:query -p deepseek

# OpenRouter (default model: openai/gpt-4o-mini)
ragsentry run -e evalset.jsonl -a app.rag:query -p openrouter
```

### Model Override

Use `-m` / `--judge-model` to keep a provider preset while changing the model:

```bash
# Groq with a 70B model
ragsentry run -e evalset.jsonl -a app.rag:query -p groq -m llama-3.3-70b-versatile

# Anthropic Sonnet
ragsentry run -e evalset.jsonl -a app.rag:query -p anthropic -m claude-3-5-sonnet-latest

# OpenRouter with a specific model
ragsentry run -e evalset.jsonl -a app.rag:query -p openrouter -m openai/gpt-4o
```

### Environment Variables

Each provider reads its API key from a standard environment variable automatically:

| Provider | Environment Variable | Default Model | Base URL |
| :--- | :--- | :--- | :--- |
| `openai` | `OPENAI_API_KEY` | `gpt-4o-mini` | Official OpenAI API |
| `anthropic` | `ANTHROPIC_API_KEY` | `claude-3-5-haiku-latest` | Official Anthropic API |
| `gemini` | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | `gemini-1.5-flash` | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `groq` | `GROQ_API_KEY` | `llama-3.1-8b-instant` | `https://api.groq.com/openai/v1` |
| `xai` | `XAI_API_KEY` | `grok-2-latest` | `https://api.x.ai/v1` |
| `ollama` | *(none required)* | `llama3.2` | `http://localhost:11434/v1` |
| `deepseek` | `DEEPSEEK_API_KEY` | `deepseek-chat` | `https://api.deepseek.com/v1` |
| `openrouter` | `OPENROUTER_API_KEY` | `openai/gpt-4o-mini` | `https://openrouter.ai/api/v1` |

### JSON Config File

Specify the provider and model in a JSON file to avoid repeating flags:

```json
{
  "provider": "gemini",
  "model": "gemini-1.5-flash",
  "temperature": 0.0
}
```

For a custom self-hosted or OpenAI-compatible endpoint:

```json
{
  "provider": "local",
  "model": "my-local-model",
  "api_base": "http://localhost:8000/v1",
  "api_key": "dummy"
}
```

---

## Storage Backends

RagSentry supports two storage backends for persisting evaluation runs, selected with the `--storage` flag on `run`, `diff`, and `ci` commands.

### Local File Storage (Default)

Runs are saved as JSON files in a local directory. No extra dependencies required.

```bash
# Explicit (same as omitting --storage entirely)
ragsentry run -e evalset.jsonl -a app.rag:query --storage local

# Specify a custom output directory
ragsentry run -e evalset.jsonl -a app.rag:query --output-dir ./my_runs
```

**Directory layout:**

```
runs/
  run_20240915_143022_abc123/
    result.json       # Scores and metadata for this run
```

Each `result.json` contains:

- `run_id` — unique identifier (timestamp + hash)
- `summary.average_scores` — per-metric averages across all questions
- `rows` — per-question scores and retrieved contexts
- `metadata` — adapter path, eval set, provider, model, timestamp

### PostgreSQL Storage

Runs are persisted to a PostgreSQL database, enabling team-wide run history, long-term trend tracking, and concurrent CI pipelines.

**Requires:** `psycopg[binary]` (installed automatically with the `postgres` extra)

```bash
pip install "ragsentry[postgres]"
```

#### Connection string

Pass a standard PostgreSQL DSN via `--storage`:

```bash
# Standard PostgreSQL URL
ragsentry run -e evalset.jsonl -a app.rag:query \
  --storage "postgresql://user:password@host:5432/dbname"

# With SSL (recommended for cloud databases)
ragsentry run -e evalset.jsonl -a app.rag:query \
  --storage "postgresql://user:password@host:5432/dbname?sslmode=require"
```

#### Environment variable (recommended for CI)

Store the DSN in an environment variable to avoid exposing credentials in command history:

```bash
export RAGSENTRY_DB_URL="postgresql://user:password@host:5432/dbname"
ragsentry run -e evalset.jsonl -a app.rag:query --storage "$RAGSENTRY_DB_URL"
```

In GitHub Actions or GitLab CI:

```yaml
env:
  RAGSENTRY_DB_URL: ${{ secrets.RAGSENTRY_DB_URL }}

steps:
  - run: ragsentry run -e evalset.jsonl -a app.rag:query --storage "$RAGSENTRY_DB_URL"
```

#### Schema

RagSentry creates the required table automatically on first use — no migrations needed:

```sql
CREATE TABLE IF NOT EXISTS ragsentry_runs (
    run_id      TEXT PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload     JSONB NOT NULL
);
```

#### Diffing and CI with PostgreSQL runs

All commands that accept run IDs work identically with PostgreSQL storage:

```bash
# Diff two runs stored in PostgreSQL
ragsentry diff run_20240901_abc run_20240915_xyz \
  --storage "postgresql://user:pass@host/dbname"

# CI gate comparing against a PostgreSQL baseline
ragsentry ci run_20240915_xyz \
  --baseline run_20240901_abc \
  --storage "postgresql://user:pass@host/dbname" \
  --threshold "faithfulness=0.80"
```

#### Storage backend comparison

| Feature | Local File | PostgreSQL |
| :--- | :---: | :---: |
| No extra dependencies | Yes | No |
| Works offline | Yes | No |
| Shared across team / CI workers | No | Yes |
| Long-term run history | Limited | Yes |
| Query and filter runs via SQL | No | Yes |
| Setup effort | None | DSN only |

---

## CI Gate Options

The `ragsentry ci` command accepts the following options to control quality gates:

| Flag | Type | Description |
| :--- | :--- | :--- |
| `--threshold` / `-t` | `metric=value` | Absolute minimum score. Repeatable. Example: `faithfulness=0.8` |
| `--baseline` / `-b` | `run_id` | Run ID to compare against for regression detection |
| `--max-regression` | `float` | Maximum allowed per-metric average score drop vs. baseline (e.g. `0.05`) |
| `--max-regressed-questions` | `int` | Maximum number of questions allowed to regress vs. baseline (default: `0`) |
| `--storage` | `str` | Storage backend: `"local"` or a `postgresql://` DSN |
| `--output-dir` | `path` | Directory for local run storage (default: `runs/`) |
| `--report` | `path` | Write a Markdown PR comment report to this file |

### Threshold syntax

```bash
# Single threshold
ragsentry ci <run_id> --threshold faithfulness=0.80

# Multiple thresholds (repeat the flag)
ragsentry ci <run_id> \
  --threshold faithfulness=0.80 \
  --threshold answer_relevancy=0.75 \
  --threshold context_precision=0.70

# Colon separator is also accepted
ragsentry ci <run_id> --threshold "faithfulness:0.80"
```

### Exit codes

| Code | Meaning |
| :--- | :--- |
| `0` | All gates passed — safe to merge |
| `1` | One or more gates failed — block the PR |

