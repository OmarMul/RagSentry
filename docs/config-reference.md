# Configuration Reference

## Judge Model Providers

RagSentry scores RAG answers using a swappable judge LLM via RAGAS. You can switch between providers effortlessly with a single CLI flag (`-p` / `--judge-provider`) or through a config file.

### 1-Click CLI Switching

Switch providers instantly without configuring URLs:

```powershell
# 1. OpenAI (default: gpt-4o-mini)
ragsentry run -e evalset.jsonl -a app.rag:query -p openai

# 2. Anthropic Claude (default: claude-3-5-haiku-latest)
ragsentry run -e evalset.jsonl -a app.rag:query -p anthropic

# 3. Google Gemini (default: gemini-1.5-flash)
ragsentry run -e evalset.jsonl -a app.rag:query -p gemini

# 4. Groq (default: llama-3.1-8b-instant)
ragsentry run -e evalset.jsonl -a app.rag:query -p groq

# 5. xAI Grok (default: grok-2-latest)
ragsentry run -e evalset.jsonl -a app.rag:query -p xai

# 6. Local Ollama (default: llama3.2 on localhost:11434)
ragsentry run -e evalset.jsonl -a app.rag:query -p ollama

# 7. DeepSeek (default: deepseek-chat)
ragsentry run -e evalset.jsonl -a app.rag:query -p deepseek

# 8. OpenRouter (default: openai/gpt-4o-mini)
ragsentry run -e evalset.jsonl -a app.rag:query -p openrouter
```

### Model Override

You can keep the provider preset and change the model using `-m` / `--judge-model`:
```powershell
# Use Groq with a 70B model:
ragsentry run -e evalset.jsonl -a app.rag:query -p groq -m llama-3.3-70b-versatile

# Use Anthropic with Sonnet:
ragsentry run -e evalset.jsonl -a app.rag:query -p anthropic -m claude-3-5-sonnet-latest

# Use OpenRouter with a specific model:
ragsentry run -e evalset.jsonl -a app.rag:query -p openrouter -m openai/gpt-4o
```

### Environment Variables

Each provider reads from its standard environment variable automatically:

| Provider | Default Env Var | Default Model | Base URL |
| :--- | :--- | :--- | :--- |
| `openai` | `OPENAI_API_KEY` | `gpt-4o-mini` | Official OpenAI API |
| `anthropic` | `ANTHROPIC_API_KEY` | `claude-3-5-haiku-latest` | Official Anthropic API |
| `gemini` | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | `gemini-1.5-flash` | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `groq` | `GROQ_API_KEY` | `llama-3.1-8b-instant` | `https://api.groq.com/openai/v1` |
| `xai` | `XAI_API_KEY` | `grok-2-latest` | `https://api.x.ai/v1` |
| `ollama` | *(none required)* | `llama3.2` | `http://localhost:11434/v1` |
| `deepseek` | `DEEPSEEK_API_KEY` | `deepseek-chat` | `https://api.deepseek.com/v1` |
| `openrouter` | `OPENROUTER_API_KEY` | `openai/gpt-4o-mini` | `https://openrouter.ai/api/v1` |

### JSON Config Example (`judge_config.json`)

You can also specify the provider inside a JSON file:

```json
{
  "provider": "gemini",
  "model": "gemini-1.5-flash",
  "temperature": 0.0
}
```

Or for a custom self-hosted endpoint:
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

RagSentry supports two storage backends for persisting evaluation runs. The backend is selected with the `--storage` flag on `run`, `diff`, and `ci` commands.

### Local File Storage (Default)

Runs are saved as JSON files in a local directory. This is the default and requires no extra dependencies.

```powershell
# Explicit (same as omitting --storage entirely):
ragsentry run -e evalset.jsonl -a app.rag:query --storage local

# Specify a custom output directory:
ragsentry run -e evalset.jsonl -a app.rag:query --output-dir ./my_runs
```

**Directory layout:**
```
runs/
  run_20240915_143022_abc123/
    result.json       # Scores + metadata for this run
```

Each `result.json` contains:
- `run_id` — unique identifier (timestamp + hash)
- `summary.average_scores` — per-metric averages across all questions
- `rows` — per-question scores and retrieved contexts
- `metadata` — adapter path, eval set, provider, model, timestamp

### PostgreSQL Storage

Runs are persisted to a PostgreSQL database, enabling team-wide run history, long-term trend tracking, and concurrent CI pipelines.

**Requires:** `psycopg[binary]` (installed automatically with the `postgres` extra)

```powershell
pip install "ragsentry[postgres]"
```

#### Connection String

Pass a standard PostgreSQL DSN via `--storage`:

```powershell
# Standard PostgreSQL URL:
ragsentry run -e evalset.jsonl -a app.rag:query \
  --storage "postgresql://user:password@host:5432/dbname"

# With SSL (recommended for cloud databases):
ragsentry run -e evalset.jsonl -a app.rag:query \
  --storage "postgresql://user:password@host:5432/dbname?sslmode=require"
```

#### Environment Variable (Recommended for CI)

Store the DSN in an environment variable to avoid exposing credentials:

```powershell
# PowerShell — set once per session:
$env:RAGSENTRY_DB_URL = "postgresql://user:password@host:5432/dbname"

# Then pass it into the command:
ragsentry run -e evalset.jsonl -a app.rag:query --storage $env:RAGSENTRY_DB_URL
```

In GitHub Actions / GitLab CI:

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

#### Diffing and CI Against Postgres Runs

All commands that accept run IDs work identically with Postgres storage:

```powershell
# Diff two runs stored in Postgres:
ragsentry diff run_20240901_abc run_20240915_xyz \
  --storage "postgresql://user:pass@host/dbname"

# CI gate comparing against a Postgres baseline:
ragsentry ci run_20240915_xyz \
  --baseline run_20240901_abc \
  --storage "postgresql://user:pass@host/dbname" \
  --threshold "faithfulness=0.80"
```

#### Storage Backend Comparison

| Feature | Local File | PostgreSQL |
| :--- | :---: | :---: |
| No extra dependencies | ✅ | ❌ |
| Works offline | ✅ | ❌ |
| Shared across team / CI workers | ❌ | ✅ |
| Long-term run history | Limited | ✅ |
| Query & filter runs via SQL | ❌ | ✅ |
| Setup effort | None | DSN only |

---

## CI Gate Options

The `ragsentry ci` command accepts the following options to control quality gates:

| Flag | Type | Description |
| :--- | :--- | :--- |
| `--threshold` / `-t` | `metric=value` | Absolute minimum score. Can be repeated. E.g. `faithfulness=0.8` |
| `--baseline` / `-b` | `run_id` | Run ID to compare against for regression detection |
| `--max-regression` | `float` | Maximum allowed per-metric average score drop vs. baseline (e.g. `0.05`) |
| `--max-regressed-questions` | `int` | Max number of questions allowed to regress vs. baseline (default: `0`) |
| `--storage` | `str` | Storage backend: `"local"` or a `postgresql://` DSN |
| `--output-dir` | `path` | Directory for local run storage (default: `runs/`) |
| `--report` | `path` | Write a Markdown PR comment report to this file |

### Threshold Syntax

```powershell
# Single threshold:
ragsentry ci <run_id> --threshold faithfulness=0.80

# Multiple thresholds (repeat the flag):
ragsentry ci <run_id> \
  --threshold faithfulness=0.80 \
  --threshold answer_relevancy=0.75 \
  --threshold context_precision=0.70

# Colon separator is also accepted:
ragsentry ci <run_id> --threshold "faithfulness:0.80"
```

### Exit Codes

| Code | Meaning |
| :--- | :--- |
| `0` | All gates passed — safe to merge |
| `1` | One or more gates failed — block the PR |
