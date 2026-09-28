# Installing the Adapter Scaffolder Agent Skill

RagSentry includes an AI coder skill called **`adapter-scaffolder`** designed to help AI coding assistants (such as Antigravity, AGY, Claude Code, Cursor, Windsurf, etc.) inspect an unfamiliar RAG codebase, locate retrieval entrypoints, and automatically generate a working `ragsentry_adapter.py`.

---

## Method 1 — Quick Install via RagSentry CLI (Recommended)

Once RagSentry is installed (`pip install ragsentry`), run the skill installer directly:

### 1. Install into your project workspace (Default)

```bash
# Installs to .agents/skills/adapter-scaffolder (Antigravity / AGY / Standard agents)
ragsentry install-skill
```

or using the `skill` subgroup:

```bash
ragsentry skill install
```

### 2. Install for specific AI Coder Agents

Select your agent framework using the `--agent` (`-a`) option:

```bash
# Antigravity / AGY / Standard agents (.agents/skills/adapter-scaffolder)
ragsentry install-skill --agent antigravity

# Claude Code (.claude/skills/adapter-scaffolder)
ragsentry install-skill --agent claude

# Cursor (.cursor/skills/adapter-scaffolder)
ragsentry install-skill --agent cursor

# Windsurf (.windsurfrules/adapter-scaffolder)
ragsentry install-skill --agent windsurf
```

### 3. Global Installation across all projects

Install into your home directory so your agent can use the skill in any workspace:

```bash
ragsentry install-skill --global
```

### 4. Custom Destination Path

Specify an explicit path:

```bash
ragsentry install-skill --target-dir ./my-agent-skills/adapter-scaffolder
```

---

## Method 2 — Direct Repository Copy / Git Clone

If you want to install the skill manually without running `pip install ragsentry`:

1. Clone or download the `skills/adapter-scaffolder` directory from the [RagSentry repository](https://github.com/OmarMul/RagSentry).
2. Copy `skills/adapter-scaffolder` into your agent's skill directory:

```bash
# For Antigravity / AGY agents:
mkdir -p .agents/skills
cp -r skills/adapter-scaffolder .agents/skills/

# For Claude Code:
mkdir -p .claude/skills
cp -r skills/adapter-scaffolder .claude/skills/
```

---

## How Coder Agents Use the Skill

When installed, your AI coding assistant will follow the 4-phase procedure defined in `SKILL.md`:

1. **Phase 1 — Discovery:** Scans your codebase for retrieval patterns (`retrieve`, `search`, `query`, `embedding`, `vector`).
2. **Phase 2 — Adapter Form Selection:** Chooses between **Python Callable**, **HTTP Endpoint**, or **Shell Subprocess**.
3. **Phase 3 — Scaffolding:** Fills in the appropriate starter template from `templates/` and generates `ragsentry_adapter.py`.
4. **Phase 4 — Verification:** Executes a smoke test (`ragsentry run -e evalset.jsonl -a ragsentry_adapter:query --no-scoring`) to confirm contract compliance.
