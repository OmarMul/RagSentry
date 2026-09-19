# RagSentry — Build Plan

## 1. Project Description & Design Principles

**RagSentry** is a regression-testing and evaluation tool for Retrieval-Augmented
Generation (RAG) systems that the user did not build with RagSentry itself —
"pytest for RAG." It is pointed at an already-running RAG application through a
thin adapter, scores its answers on a user-supplied evaluation set, persists every
run, diffs runs against each other, and can gate CI on quality regressions.

RagSentry never owns or ships a retrieval pipeline. It has no opinion on
frameworks, vector stores, or model providers — its entire relationship to the
target system is a JSON-in/JSON-out contract.

### Design principles

1. **Adapter, not integration.** The target system is a black box behind a
   `query(question) -> {answer, contexts, metadata?}` contract. RagSentry never
   imports LangChain, a vector store SDK, or any RAG framework as a runtime
   dependency of the core product.
2. **Zero required infrastructure.** A single `pip install` and a local folder of
   JSON/Parquet files is enough to run evaluations and diffs. Postgres, Docker,
   and hosted tracing are optional plugins, never defaults.
3. **One LLM dependency, and it's swappable.** The judge model used for
   faithfulness/relevancy scoring is the only place RagSentry calls an LLM, and
   it's selected via config (model name + API base + API key env var), never
   hardcoded to one provider or router.
4. **Build on RAGAS for metric math, not around it.** RagSentry owns
   orchestration, storage, diffing, and CI wiring. It does not reimplement
   faithfulness/relevancy/precision/recall scoring — it calls a metrics library.
5. **Every milestone is a working slice.** After any milestone, `ragsentry` does
   something real end-to-end from the CLI. No milestone is "plumbing only."
6. **The test fixture is not the product.** The tiny hand-rolled RAG app used to
   develop/test RagSentry lives in `examples/` or `tests/fixtures/`, is
   explicitly labeled as a fixture, and never leaks into the core package's
   dependencies.

---

## 2. Proposed Repository Structure

```
RagSentry/
├── pyproject.toml
├── README.md
├── LICENSE
├── ragsentry/                      # the installable package — the product
│   ├── __init__.py
│   ├── cli.py                      # `ragsentry` entrypoint (run, diff, ci, init)
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py                 # Adapter protocol: query(question) -> dict
│   │   ├── python_callable.py      # wraps a user-supplied Python function
│   │   ├── http.py                 # POST + configurable JSONPath extraction
│   │   └── shell.py                # subprocess adapter, stdin/stdout JSON
│   ├── evalset/
│   │   ├── __init__.py
│   │   ├── loader.py                # load JSON/JSONL/CSV Q&A sets
│   │   └── schema.py                 # pydantic models for eval-set rows
│   ├── metrics/
│   │   ├── __init__.py
│   │   ├── ragas_backend.py          # wraps RAGAS metrics (faithfulness, etc.)
│   │   └── judge_config.py           # provider-agnostic judge-model config
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── base.py                   # RunStore protocol
│   │   ├── local_file.py             # default: JSON/Parquet on disk
│   │   └── postgres.py               # optional backend, extra dependency
│   ├── runner.py                     # orchestrates: evalset x adapter -> scored run
│   ├── diff.py                       # compares two persisted runs
│   ├── ci.py                         # threshold/baseline gate + exit codes
│   └── report/
│       ├── __init__.py
│       ├── console.py                # human-readable terminal summary
│       └── pr_comment.py             # markdown formatter for PR comments
├── skills/
│   └── adapter-scaffolder/           # optional agent-usable skill
│       ├── SKILL.md
│       └── templates/
├── examples/
│   └── toy_rag_fixture/              # minimal hand-rolled retriever, dev/test only
│       ├── README.md                 # explicitly labeled "not the product"
│       ├── toy_retriever.py
│       └── sample_evalset.jsonl
├── .github/
│   └── workflows/
│       └── ragsentry-self-check.yml  # dogfoods RagSentry's own CI gate
├── docs/
│   ├── adapter-contract.md
│   ├── ci-integration.md
│   └── config-reference.md
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

---

## 3. Milestones

Each milestone is independently demoable: if development stopped right after it,
what exists is a coherent, working piece of RagSentry — not a partial internal
module.

### Milestone 0 — Repo Skeleton & Adapter Contract

**Goal:** Define the adapter contract as executable code and ship the
project's own toy fixture to exercise it.

**Files to create:**

- `pyproject.toml` (package metadata, no RAG-framework dependencies)
- `ragsentry/adapters/base.py` — `Adapter` protocol with `query(question: str) -> AdapterResponse`
- `ragsentry/adapters/python_callable.py`
- `examples/toy_rag_fixture/toy_retriever.py` — ~30 lines, in-memory keyword
  retriever, no vector DB, no external LLM call required to run
- `docs/adapter-contract.md`

**Done when:** `python -c "from ragsentry.adapters.python_callable import PythonCallableAdapter; ..."` runs the toy fixture through the adapter and
prints a valid `{answer, contexts, metadata}` dict for a hardcoded question.

---

### Milestone 1 — Eval Set Loading + Local Run (no scoring yet)

**Goal:** Load a user's Q&A eval set and run every question through an adapter,
persisting raw (unscored) results locally.

**Files to create/edit:**

- `ragsentry/evalset/schema.py`, `ragsentry/evalset/loader.py` (JSONL first;
  CSV can follow)
- `ragsentry/storage/base.py`, `ragsentry/storage/local_file.py`
- `ragsentry/runner.py` (adapter × evalset → raw run, no metrics yet)
- `ragsentry/cli.py` — `ragsentry run --evalset path --adapter path --out runs/`
- `examples/toy_rag_fixture/sample_evalset.jsonl`

**Done when:** `ragsentry run --evalset examples/toy_rag_fixture/sample_evalset.jsonl --adapter examples.toy_rag_fixture.toy_retriever:query` produces a timestamped
run file under `runs/` containing question, answer, and contexts for every row,
with zero infrastructure beyond the local filesystem.

---

### Milestone 2 — Scoring with RAGAS (the one LLM dependency)

**Goal:** Score each run's answers with faithfulness, answer relevancy, context
precision, and context recall, using a swappable, provider-agnostic judge model.

**Files to create/edit:**

- `ragsentry/metrics/judge_config.py` — reads model name / API base / API key
  env var from a config file or CLI flags; no provider hardcoded
- `ragsentry/metrics/ragas_backend.py` — wraps RAGAS's metric functions
- `ragsentry/runner.py` (edit: attach scores to each run row)
- `docs/config-reference.md`

**Done when:** the same `ragsentry run` command, given a `--judge-config`
pointing at any OpenAI-compatible endpoint (tested against two different
providers to prove swappability), produces a run file where every row carries
the four RAGAS scores.

**Hard-dependency callout:** RAGAS itself pulls in `langchain-core` as a
transitive dependency for its LLM-wrapper classes. This is unavoidable if RAGAS
is used as-is — but it must stay invisible to the user's own RAG stack (i.e.
`langchain-core` is a scoring-internals detail, never imported or required in
`ragsentry/adapters/`). Call this out explicitly in `docs/config-reference.md`
so users understand it's RAGAS's dependency, not a RagSentry opinion about
their architecture. Pin it loosely and revisit if RAGAS ships a
framework-agnostic client in the future.

---

### Milestone 3 — HTTP and Shell Adapters

**Goal:** Complete the three-form adapter contract from the spec.

**Files to create/edit:**

- `ragsentry/adapters/http.py` — configurable JSONPath (or simple dotted-path)
  extraction for `answer`/`contexts` from an arbitrary response shape
- `ragsentry/adapters/shell.py` — subprocess, question on stdin or arg,
  JSON on stdout
- `docs/adapter-contract.md` (edit: document all three forms with copy-paste
  configs)
- `tests/integration/test_adapters.py`

**Done when:** the toy fixture is wrapped once as a tiny Flask/FastAPI-free
`http.server` endpoint and once as a shell script, and `ragsentry run` produces
identical scored output through all three adapter types for the same eval set.

**Hard-dependency callout:** the HTTP adapter needs an HTTP client. Use
`httpx` or even `urllib` from the standard library rather than pulling in a
larger framework — this adapter is a *client*, it should not require a web
framework.

---

### Milestone 4 — Run Diffing

**Goal:** Compare two persisted runs and show per-question score deltas.

**Files to create/edit:**

- `ragsentry/diff.py` — matches rows by question ID, computes per-metric deltas,
  buckets into improved / regressed / unchanged / new / removed
- `ragsentry/report/console.py` — human-readable diff table
- `ragsentry/cli.py` (edit: add `ragsentry diff run_a.json run_b.json`)

**Done when:** running two scored evaluations of the toy fixture (before/after
a deliberate change to `toy_retriever.py`) and diffing them prints a table
naming exactly which questions changed and by how much on each metric.

---

### Milestone 5 — CI Gate + PR Comment

**Goal:** Fail a build on regression, either against a fixed threshold or
against a stored baseline run, and format the result as a PR comment.

**Files to create/edit:**

- `ragsentry/ci.py` — threshold config, baseline-run lookup, non-zero exit
  code on breach
- `ragsentry/report/pr_comment.py` — markdown-formatted regression summary
- `ragsentry/cli.py` (edit: add `ragsentry ci --baseline path --thresholds path` with proper exit codes)
- `.github/workflows/ragsentry-self-check.yml` — RagSentry gating its own
  toy-fixture eval set, as a real dogfooding example
- `docs/ci-integration.md`

**Done when:** a GitHub Actions run against a deliberately regressed toy
fixture fails the job and the workflow log/PR comment names the specific
regressed questions and metrics; a non-regressed run passes.

**Hard-dependency callout:** none required for the gate logic itself — keep
`ragsentry ci` CI-provider-agnostic (plain exit codes + a markdown string on
stdout). The GitHub Actions workflow is one *consumer* of that, not a
dependency of the core package. Posting the comment via `gh` CLI or a curl
call to the GitHub API keeps `pyproject.toml` free of a GitHub SDK.

---

### Milestone 6 — Optional Postgres Storage Backend

**Goal:** Prove the local-file storage abstraction is real by swapping in a
heavier backend without touching `runner.py`, `diff.py`, or `ci.py`.

**Files to create/edit:**

- `ragsentry/storage/postgres.py`
- `pyproject.toml` (edit: add `ragsentry[postgres]` extra, not a base
  dependency)
- `docs/config-reference.md` (edit: document `--storage postgres` flag)

**Done when:** `ragsentry run --storage postgres://...` and `ragsentry run --storage local` produce runs that `ragsentry diff` and `ragsentry ci` can
both consume identically, and the base install (no extras) never imports
`psycopg`.

---

### Milestone 7 — Agent-Usable Adapter-Scaffolder Skill

**Goal:** An optional skill/procedure an agent (e.g. a coding assistant) can
follow to inspect an unfamiliar codebase, locate where retrieval happens, and
scaffold a working adapter file.

**Files to create/edit:**

- `skills/adapter-scaffolder/SKILL.md` — step-by-step procedure: locate the
  retrieval call site, identify how the answer and source chunks are produced,
  emit a `ragsentry_adapter.py` matching one of the three contract forms
- `skills/adapter-scaffolder/templates/` — adapter templates the skill fills in

**Done when:** running the skill against a second, different toy fixture (not
`examples/toy_rag_fixture`, to prove it isn't hardcoded to it) produces a
working adapter file on the first pass, verified by `ragsentry run` against it.

---

### Milestone 8 — Packaging, Docs Pass, and `ragsentry init`

**Goal:** Make the five-minute wiring promise real for a first-time user.

**Files to create/edit:**

- `ragsentry/cli.py` (edit: add `ragsentry init` — interactive prompt that
  scaffolds an adapter stub + starter config)
- `README.md` — quickstart that goes from `pip install ragsentry` to a first
  scored run in under five commands
- `docs/*.md` — final consistency pass
- publish to PyPI (or at least a clean `pip install .` from a fresh clone)

**Done when:** a person unfamiliar with the project can go from a fresh clone
to a scored run of the toy fixture using only the README, with no other
context, in under five minutes.

---

## 4. Pacing Suggestion

RagSentry is a smaller, sharper scope than a full RAG platform, so milestones
are sized for a few focused evenings rather than full weekends each.

| Milestone                        | Effort estimate                                            |
| -------------------------------- | ---------------------------------------------------------- |
| 0 — Skeleton & adapter contract | 1 evening                                                  |
| 1 — Eval set loading + raw run  | 1 evening                                                  |
| 2 — RAGAS scoring               | 1–2 evenings (judge-config plumbing takes the extra time) |
| 3 — HTTP + shell adapters       | 1 evening                                                  |
| 4 — Run diffing                 | 1 evening                                                  |
| 5 — CI gate + PR comment        | 1–2 evenings                                              |
| 6 — Optional Postgres backend   | 1 evening                                                  |
| 7 — Adapter-scaffolder skill    | 1–2 evenings                                              |
| 8 — Packaging & docs pass       | 1 evening                                                  |

Total: roughly **2–3 weekends'** worth of evening sessions, noticeably lighter
than a 10-milestone, one-weekend-per-milestone platform build, because
RagSentry deliberately has no framework comparisons, no multi-vector-store
support, and no tracing UI to build.

---

## 5. Hard-Dependency Callouts (Summary)

| Where                                  | Risk                                          | Lighter alternative                                                                                                                                    |
| -------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Metrics (`metrics/ragas_backend.py`) | RAGAS transitively pulls in`langchain-core` | Unavoidable while using RAGAS as-is; isolate it to the metrics module, document it as a scoring-internals dependency, never let it touch`adapters/`  |
| HTTP adapter (`adapters/http.py`)    | Tempting to require a web framework           | Use`httpx` (or stdlib `urllib`) — this is a client, not a server                                                                                  |
| Storage (`storage/postgres.py`)      | Could become a default dependency             | Ship as a`ragsentry[postgres]` extra; base install stays file-based only                                                                             |
| CI gate (`ci.py`)                    | Could couple to GitHub's API SDK              | Keep the gate provider-agnostic (exit code + markdown string); use`gh` CLI or a plain HTTP call in the *workflow*, not the package                 |
| Eval set loading                       | Could require pandas for CSV support          | Start with JSONL only (Milestone 1); add CSV via stdlib`csv` module rather than pandas unless a later milestone genuinely needs dataframe operations |
