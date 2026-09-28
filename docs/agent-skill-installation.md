# Agent Skill Installation

RagSentry includes a skill called **`adapter-scaffolder`** designed to help AI coding assistants (Antigravity, AGY, Claude Code, Cursor, Windsurf, and others) inspect an unfamiliar RAG codebase, locate the retrieval entry point, and automatically generate a working `ragsentry_adapter.py`.

---

## Table of Contents

- [Method 1: Install via RagSentry CLI (Recommended)](#method-1-install-via-ragsentry-cli-recommended)
- [Method 2: Manual Repository Copy](#method-2-manual-repository-copy)
- [How Agents Use the Skill](#how-agents-use-the-skill)

---

## Method 1: Install via RagSentry CLI (Recommended)

Once RagSentry is installed (`pip install ragsentry`), run the skill installer directly from your project root.

### Install into your workspace (default)

```bash
# Installs to .agents/skills/adapter-scaffolder
ragsentry install-skill
```

The `skill install` subcommand is an alias for the same operation:

```bash
ragsentry skill install
```

### Install for a specific agent

Use the `--agent` (`-a`) flag to target a specific agent's configuration directory:

```bash
# Antigravity / AGY (.agents/skills/adapter-scaffolder)
ragsentry install-skill --agent antigravity

# Claude Code (.claude/skills/adapter-scaffolder)
ragsentry install-skill --agent claude

# Cursor (.cursor/skills/adapter-scaffolder)
ragsentry install-skill --agent cursor

# Windsurf (.windsurfrules/adapter-scaffolder)
ragsentry install-skill --agent windsurf
```

### Install globally

Install into your home directory so the skill is available in every workspace:

```bash
ragsentry install-skill --global
```

### Install to a custom path

Specify an explicit destination directory:

```bash
ragsentry install-skill --target-dir ./my-agent-skills/adapter-scaffolder
```

---

## Method 2: Manual Repository Copy

If you want to install the skill without running `pip install ragsentry`:

1. Clone or download the `skills/adapter-scaffolder` directory from the [RagSentry repository](https://github.com/OmarMul/RagSentry).
2. Copy it into your agent's skill directory:

```bash
# For Antigravity / AGY
mkdir -p .agents/skills
cp -r skills/adapter-scaffolder .agents/skills/

# For Claude Code
mkdir -p .claude/skills
cp -r skills/adapter-scaffolder .claude/skills/
```

---

## How Agents Use the Skill

When the skill is installed, your AI coding assistant reads `SKILL.md` and follows a four-phase procedure:

| Phase | Name | Description |
| :---: | :--- | :--- |
| 1 | Discovery | Scans the codebase for retrieval patterns (`retrieve`, `search`, `query`, `embedding`, `vector`) to locate the RAG entry point. |
| 2 | Adapter Form Selection | Chooses between Python Callable, HTTP Endpoint, or Shell Subprocess based on how the RAG system is exposed. |
| 3 | Scaffolding | Fills in the appropriate template from `templates/` and writes `ragsentry_adapter.py`. |
| 4 | Verification | Runs a smoke test (`ragsentry run -e evalset.jsonl -a ragsentry_adapter:query --no-scoring`) to confirm contract compliance. |

See the [Adapter Scaffolder Skill specification](../skills/adapter-scaffolder/SKILL.md) for the full procedure the agent follows.

