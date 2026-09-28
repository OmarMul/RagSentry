import sys
from click.testing import CliRunner
from ragsentry.cli import cli


def test_cli_init_command(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--directory", str(tmp_path)])
    assert result.exit_code == 0
    assert "RagSentry initialization complete!" in result.output

    adapter_path = tmp_path / "ragsentry_adapter.py"
    evalset_path = tmp_path / "evalset.jsonl"
    assert adapter_path.exists()
    assert evalset_path.exists()


def test_cli_run_command_no_scoring(tmp_path):
    runner = CliRunner()
    # Init in tmp_path
    runner.invoke(cli, ["init", "--directory", str(tmp_path)])

    evalset = tmp_path / "evalset.jsonl"
    out_dir = tmp_path / "runs"

    # Add tmp_path to sys.path so PythonCallableAdapter can import ragsentry_adapter
    if str(tmp_path) not in sys.path:
        sys.path.insert(0, str(tmp_path))

    result = runner.invoke(
        cli,
        [
            "run",
            "-e", str(evalset),
            "-a", "ragsentry_adapter:query",
            "-o", str(out_dir),
            "--no-scoring",
        ],
    )
    assert result.exit_code == 0, f"Command failed output: {result.output}"
    assert "Evaluation complete!" in result.output


def test_cli_install_skill_command(tmp_path):
    runner = CliRunner()
    target_dir = tmp_path / "installed_skill"
    result = runner.invoke(cli, ["install-skill", "--target-dir", str(target_dir)])
    assert result.exit_code == 0
    assert "Successfully installed 'adapter-scaffolder' skill" in result.output
    assert (target_dir / "SKILL.md").exists()

