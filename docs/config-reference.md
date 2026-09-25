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
