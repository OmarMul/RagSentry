from __future__ import annotations

import click
from pathlib import Path

from ragsentry.adapters.base import Adapter
from ragsentry.adapters.http import HttpAdapter
from ragsentry.adapters.python_callable import PythonCallableAdapter
from ragsentry.adapters.shell import ShellAdapter
from ragsentry.evalset.loader import load_evalset
from ragsentry.metrics.judge_config import JudgeConfig
from ragsentry.runner import run_eval
from ragsentry.storage.local_file import LocalFileRunStore
from ragsentry.diff import compare_runs
from ragsentry.report.console import format_diff_console
from ragsentry.ci import evaluate_ci_gate
from ragsentry.report.pr_comment import format_pr_comment
from ragsentry.storage import get_run_store
from ragsentry.storage.base import RunStore
from ragsentry.storage.local_file import LocalFileRunStore



def resolve_adapter(
    adapter_str: str,
    adapter_type: str | None = None,
    answer_path: str = "answer",
    contexts_path: str = "contexts",
) -> Adapter:
    """Resolve an adapter based on explicit type or string pattern."""
    a_type = (adapter_type or "").lower().strip()

    # Auto-detect if not explicitly passed
    if not a_type:
        if adapter_str.startswith("http://") or adapter_str.startswith("https://"):
            a_type = "http"
        elif adapter_str.startswith("shell:") or adapter_str.startswith("sh:"):
            a_type = "shell"
        else:
            a_type = "python"

    if a_type == "http":
        return HttpAdapter(
            url=adapter_str,
            answer_path=answer_path,
            contexts_path=contexts_path,
        )
    elif a_type == "shell":
        cmd = adapter_str
        if cmd.startswith("shell:"):
            cmd = cmd[6:]
        elif cmd.startswith("sh:"):
            cmd = cmd[3:]
        return ShellAdapter(command=cmd.strip())
    else:
        return PythonCallableAdapter(adapter_str)


@click.group()
def cli() -> None:
    """RagSentry — regression-testing and evaluation for RAG systems."""
    pass


@cli.command(name="run")
@click.option(
    "--evalset", "-e",
    required=True,
    type=click.Path(exists=True),
    help="Path to evaluation dataset (.jsonl or .json).",
)
@click.option(
    "--adapter", "-a",
    required=True,
    help="Adapter target (e.g. 'pkg.mod:func', 'http://localhost:8000/query', or 'shell:python script.py').",
)
@click.option(
    "--adapter-type",
    type=click.Choice(["python", "http", "shell"], case_sensitive=False),
    help="Explicit adapter type (default: auto-detected).",
)
@click.option(
    "--answer-path",
    default="answer",
    help="Dotted path for extracting the answer from an HTTP response (default: 'answer').",
)
@click.option(
    "--contexts-path",
    default="contexts",
    help="Dotted path for extracting contexts from an HTTP response (default: 'contexts').",
)
@click.option(
    "--out", "-o",
    default="runs",
    help="Output directory for run results (default: 'runs').",
)
@click.option(
    "--judge-provider", "-p",
    type=click.Choice(
        ["openai", "anthropic", "gemini", "groq", "xai", "ollama", "local", "deepseek", "openrouter"],
        case_sensitive=False,
    ),
    help="Provider preset: openai, anthropic, gemini, groq, xai, ollama, local, deepseek, openrouter.",
)
@click.option(
    "--judge-model", "-m",
    help="Judge model name.",
)
@click.option(
    "--api-key",
    help="Explicit API key (overrides environment variables).",
)
@click.option(
    "--api-base",
    help="Custom API base URL.",
)
@click.option(
    "--judge-config", "-j",
    type=click.Path(exists=True),
    help="Path to judge model JSON configuration file.",
)

@click.option(
    "--no-scoring",
    is_flag=True,
    help="Skip LLM judge scoring and only record raw generation and context outputs.",
)
@click.option(
    "--storage", "-s",
    default="local",
    help="Storage backend: 'local' (default) or 'postgresql://user:pass@host/db'.",
)

def run_command(
    evalset: str,
    adapter: str,
    adapter_type: str | None,
    answer_path: str,
    contexts_path: str,
    out: str,
    no_scoring: bool,
    storage: str,
    judge_provider: str | None,
    judge_model: str | None,
    api_key: str | None,
    api_base: str | None,
    judge_config: str | None,
) -> None:
    """Run an evaluation set through an adapter and persist results."""
    config: JudgeConfig | None = None

    if no_scoring:
        config = None
    elif judge_config:
        config = JudgeConfig.from_file(judge_config)
        if judge_provider:
            config.provider = judge_provider.lower()
        if judge_model:
            config.model = judge_model
        if api_key:
            config.api_key = api_key
        if api_base:
            config.api_base = api_base
    elif judge_provider or judge_model or api_key or api_base:
        config = JudgeConfig.create(
            provider=judge_provider,
            model=judge_model,
            api_base=api_base,
            api_key=api_key,
        )

    click.echo(f"[*] Resolving adapter: {adapter}")
    adapter_instance = resolve_adapter(
        adapter_str=adapter,
        adapter_type=adapter_type,
        answer_path=answer_path,
        contexts_path=contexts_path,
    )

    click.echo(f"[*] Loading eval set: {evalset}")
    items = load_evalset(evalset)
    click.echo(f"[*] Loaded {len(items)} questions.")

    if config:
        click.echo(f"[*] Scoring enabled using [{config.provider.upper()}] with model: {config.model}")
    else:
        click.echo("[*] Scoring disabled (raw run).")

    click.echo("[*] Running evaluation...")
    run_result = run_eval(
        adapter=adapter_instance,
        evalset=items,
        adapter_name=adapter,
        evalset_path=evalset,
        judge_config=config,
    )

    store = get_run_store(storage=storage, output_dir=out)
    saved_path = store.save(run_result)
    click.echo(f"[+] Evaluation complete! Run saved to: {saved_path}")

    if config and "average_scores" in run_result.summary:
        click.echo("\n--- Evaluation Summary ---")
        for metric, score in run_result.summary["average_scores"].items():
            click.echo(f"  {metric}: {score}")



@cli.command(name="diff")
@click.argument("baseline")
@click.argument("candidate")
@click.option(
    "--tolerance",
    type=float,
    default=0.001,
    help="Tolerance threshold for considering a delta unchanged (default: 0.001).",
)
@click.option(
    "--storage", "-s",
    default="local",
    help="Storage backend: 'local' (default) or 'postgresql://user:pass@host/db'.",
)
def diff_command(baseline: str, candidate: str, tolerance: float, storage: str) -> None:
    """Compare two persisted evaluation runs and display score regressions/improvements."""
    click.echo(f"[*] Comparing baseline:  {baseline}")
    click.echo(f"[*] With candidate:      {candidate}")

    store = get_run_store(storage=storage)
    base_run = store.load(baseline)
    cand_run = store.load(candidate)
    diff = compare_runs(base_run, cand_run, tolerance=tolerance)
    report = format_diff_console(diff)
    click.echo("\n" + report)




@cli.command(name="ci")
@click.option(
    "--candidate", "-c",
    required=True,
    help="Path to candidate evaluation run JSON file or Postgres run ID.",
)
@click.option(
    "--baseline", "-b",
    help="Path to baseline evaluation run JSON file or Postgres run ID (optional).",
)
@click.option(
    "--threshold", "-t",
    multiple=True,
    help="Quality threshold (e.g. '-t faithfulness=0.8 -t answer_relevancy=0.7'). Can be repeated.",
)
@click.option(
    "--max-regression",
    type=float,
    help="Maximum allowable drop in any average metric compared to baseline (e.g. 0.05).",
)
@click.option(
    "--max-regressed-questions",
    type=int,
    default=0,
    help="Maximum allowable count of regressed individual questions (default: 0).",
)
@click.option(
    "--pr-comment-out",
    type=click.Path(),
    help="Output file path to save Markdown PR comment.",
)
@click.option(
    "--storage", "-s",
    default="local",
    help="Storage backend: 'local' (default) or 'postgresql://user:pass@host/db'.",
)

def ci_command(
    candidate: str,
    baseline: str | None,
    threshold: tuple[str, ...],
    max_regression: float | None,
    max_regressed_questions: int,
    pr_comment_out: str | None,
    storage: str,
) -> None:
    """Evaluate a run against fixed thresholds and baseline regression limits for CI/CD."""
    click.echo("[*] Evaluating RagSentry CI Quality Gate...")
    click.echo(f"  Candidate Run: {candidate}")
    if baseline:
        click.echo(f"  Baseline Run:  {baseline}")

    gate_result = evaluate_ci_gate(
        candidate=candidate,
        baseline=baseline,
        thresholds=list(threshold),
        max_regression=max_regression,
        max_regressed_questions=max_regressed_questions,
        storage=storage,
    )

    # Format Markdown PR Comment
    comment_md = format_pr_comment(gate_result)

    if pr_comment_out:
        out_path = Path(pr_comment_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(comment_md, encoding="utf-8")
        click.echo(f"[+] PR comment written to: {pr_comment_out}")

    # Terminal output
    if gate_result.passed:
        click.echo("\n[+] SUCCESS: Quality gate PASSED!")
    else:
        click.echo("\n[-] FAILURE: Quality gate FAILED with violations:")
        for v in gate_result.violations:
            click.echo(f"    - {v}")

    # Exit with code 0 on success, 1 on failure
    if not gate_result.passed:
        raise click.exceptions.Exit(code=1)


@cli.command(name="init")
@click.option(
    "--directory", "-d",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Target directory to initialize (default: current directory).",
)
def init_command(directory: str) -> None:
    """Initialize RagSentry in the target directory by scaffolding starter files."""
    target_dir = Path(directory)
    adapter_file = target_dir / "ragsentry_adapter.py"
    evalset_file = target_dir / "evalset.jsonl"

    click.echo("[*] Initializing RagSentry...")

    # 1. Create starter adapter stub
    if not adapter_file.exists():
        adapter_code = '''"""
RagSentry Adapter — Starter Stub
Generated by `ragsentry init`

Usage:
    ragsentry run -e evalset.jsonl -a ragsentry_adapter:query
"""
from typing import Any


def query(question: str) -> dict[str, Any]:
    """
    RagSentry adapter contract:
    Takes a question string and returns a dict with:
        - "answer": str
        - "contexts": list[str]
    """
    # TODO: Replace with call to your RAG application
    # Example:
    #   result = my_rag_app.ask(question)
    #   return {"answer": result.answer, "contexts": result.retrieved_docs}

    return {
        "answer": f"Sample response for question: '{question}'",
        "contexts": [
            "Sample context chunk 1 retrieved for query.",
            "Sample context chunk 2 retrieved for query.",
        ],
    }


if __name__ == "__main__":
    res = query("Test question?")
    print("Contract test succeeded:", res)
'''
        adapter_file.write_text(adapter_code, encoding="utf-8")
        click.echo(f"  [+] Created starter adapter: {adapter_file}")
    else:
        click.echo(f"  [~] Adapter already exists: {adapter_file}")

    # 2. Create starter eval set
    if not evalset_file.exists():
        evalset_content = '''{"id": "q1", "question": "What is RagSentry?", "ground_truth": "RagSentry is a regression-testing and evaluation CLI for RAG systems."}
{"id": "q2", "question": "How do I run an evaluation?", "ground_truth": "Run `ragsentry run -e evalset.jsonl -a ragsentry_adapter:query`."}
'''
        evalset_file.write_text(evalset_content, encoding="utf-8")
        click.echo(f"  [+] Created starter evalset: {evalset_file}")
    else:
        click.echo(f"  [~] Evalset already exists: {evalset_file}")

    click.echo("\n[+] RagSentry initialization complete!")
    click.echo("\nNext steps:")
    click.echo("  1. Edit `ragsentry_adapter.py` to connect your RAG application.")
    click.echo("  2. Run your first evaluation:")
    click.echo("     ragsentry run -e evalset.jsonl -a ragsentry_adapter:query --no-scoring")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
