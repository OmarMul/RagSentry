import sys
import pytest
from ragsentry.adapters.python_callable import PythonCallableAdapter
from ragsentry.adapters.shell import ShellAdapter


def sample_python_rag(question: str) -> dict:
    return {
        "answer": f"Answer for: {question}",
        "contexts": [f"Context for: {question}"],
    }


def test_python_callable_adapter():
    adapter = PythonCallableAdapter("tests.unit.test_adapters:sample_python_rag")
    res = adapter.query("What is unit testing?")
    assert res.answer == "Answer for: What is unit testing?"
    assert res.contexts == ["Context for: What is unit testing?"]


def test_shell_adapter(tmp_path):
    # Create a small script that reads stdin and writes JSON to stdout
    script_path = tmp_path / "mock_rag.py"
    script_path.write_text(
        "import sys, json\n"
        "q = sys.stdin.read().strip()\n"
        "print(json.dumps({'answer': f'Shell answer for {q}', 'contexts': ['Shell context']}))\n",
        encoding="utf-8",
    )
    python_exe = sys.executable.replace("\\", "/")
    script_str = str(script_path).replace("\\", "/")
    adapter = ShellAdapter(command=f"{python_exe} {script_str}")
    res = adapter.query("Hello Shell")
    assert "Shell answer for" in res.answer
    assert res.contexts == ["Shell context"]
