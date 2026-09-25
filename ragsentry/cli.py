from __future__ import annotations

import click

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

def run_command(
    evalset: str,
    adapter: str,
    adapter_type: str | None,
    answer_path: str,
    contexts_path: str,
    out: str,
    judge_provider: str | None,
    judge_model: str | None,
    api_key: str | None,
    api_base: str | None,
    judge_config: str | None,
) -> None:
    """Run an evaluation set through an adapter and persist results."""
    config: JudgeConfig | None = None

    if judge_config:
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

    store = LocalFileRunStore(output_dir=out)
    saved_path = store.save(run_result)
    click.echo(f"[+] Evaluation complete! Run saved to: {saved_path}")

    if config and "average_scores" in run_result.summary:
        click.echo("\n--- Evaluation Summary ---")
        for metric, score in run_result.summary["average_scores"].items():
            click.echo(f"  {metric}: {score}")

@cli.command(name="diff")
@click.argument("baseline", type=click.Path(exists=True))
@click.argument("candidate", type=click.Path(exists=True))
@click.option(
    "--tolerance",
    type=float,
    default=0.001,
    help="Tolerance threshold for considering a delta unchanged (default: 0.001).",
)
def diff_command(baseline: str, candidate: str, tolerance: float) -> None:
    """Compare two persisted evaluation runs and display score regressions/improvements."""
    click.echo(f"[*] Comparing baseline:  {baseline}")
    click.echo(f"[*] With candidate:      {candidate}")

    diff = compare_runs(baseline, candidate, tolerance=tolerance)
    report = format_diff_console(diff)
    click.echo("\n" + report)



def main() -> None:
    cli()


if __name__ == "__main__":
    main()
