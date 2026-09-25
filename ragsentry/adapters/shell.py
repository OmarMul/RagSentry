from __future__ import annotations

import json
import shlex
import subprocess
from typing import Any


from ragsentry.adapters.base import Adapter, AdapterResponse


class ShellAdapter(Adapter):
    """Adapter that executes an external shell command or script."""

    def __init__(
        self,
        command: str | list [str],
        pass_as: str = "stdin", #stdin or arg
        timeout: float = 30.0,
        cwd: str | None = None,
    ) -> None:

        if isinstance(command, str):
            self.command = shlex.split(command, posix=False)

        else:
            self.command = list(command)

        
        self.pass_as = pass_as.lower()
        self.timeout = timeout
        self.cwd = cwd


        if self.pass_as not in ("stdin", "arg"):
            raise ValueError(f"pass_as must be 'stdin' or 'arg', got '{pass_as}'")

    
    def query(self, question: str) -> AdapterResponse:
        cmd = list(self.command)
        input_data = None

        if self.pass_as == "arg":
            cmd.append(question)

        else:
            input_data = json.dumps({"question": question})

        proc = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=self.timeout,
            cwd=self.cwd,
        )
        
        if proc.returncode != 0:
            raise RuntimeError(
                f"Shell command failed with exit code {proc.returncode}.\nStderr: {proc.stderr}"
            )
        stdout_clean = proc.stdout.strip()
        if not stdout_clean:
            raise ValueError(f"Shell command produced no stdout output.\nStderr: {proc.stderr}")
        try:
            data: dict[str, Any] = json.loads(stdout_clean)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Shell adapter expected JSON output on stdout, got: {stdout_clean}"
            ) from exc
        if "answer" not in data or "contexts" not in data:
            raise ValueError(
                f"Shell command output missing 'answer' or 'contexts'. Keys found: {list(data.keys())}"
            )
        contexts = data["contexts"]
        if not isinstance(contexts, list):
            raise TypeError(f"'contexts' in shell output must be a list, got {type(contexts)}")
        
        
        return AdapterResponse(
            answer=str(data["answer"]),
            contexts=[str(c) for c in contexts],
            metadata=data.get("metadata", {}),
        )