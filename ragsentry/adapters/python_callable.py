from __future__ import annotations

import importlib
from typing import Any, Callable

from ragsentry.adapters.base import Adapter, AdapterResponse


class PythonCallableAdapter(Adapter):
    """Adapter that wraps an in-process Python callable."""


    def __init__(self, target: Callable[[str], dict[str, Any] | AdapterResponse] | str) -> None:

        if isinstance(target, str):
            self._callable = self._load_callable(target)
        elif callable(target):
            self._callable = target

        else:
            raise TypeError(f"Target must be a callable or an import string ('module:func'), got {type(target)}")

    

    @staticmethod
    def _load_callable(import_str: str) -> Callable[[str], Any]:
        """Resolves an import string of format 'module.submodule:function_name'."""
        if ":" not in import_str:
            raise ValueError(
                f"Invalid import string '{import_str}'. Expected format: 'package.module:function_name'"
            )
        
        module_path, func_name = import_str.split(":", 1)
        module = importlib.import_module(module_path)
        target = getattr(module, func_name)
        if not callable(target):
            raise TypeError(f"Resolved object '{import_str}' is not callable.")

        return target


    def query(self, question: str) -> AdapterResponse:

        raw = self._callable(question)

        if isinstance(raw, AdapterResponse):
            return raw

        if isinstance(raw, dict):
            if "answer" not in raw or "contexts" not in raw:
                raise ValueError(
                    f"Callable returned a dict missing 'answer' or 'contexts': keys={list(raw.keys())}"
                )
            
            contexts = raw["contexts"]
            if not isinstance(contexts, list):
                raise TypeError(f"'contexts' must be a list of strings, got {type(contexts)}")

            
            return AdapterResponse(
                answer=str(raw["answer"]),
                contexts=[str(c) for c in contexts],
                metadata=raw.get("metadata", {}),
            )


        raise TypeError(
            f"Expected callable to return dict or AdapterResponse, got {type(raw)}"
        )