from __future__ import annotations

import os
from pathlib import Path
import pytest
from ragsentry.installer import find_skill_source, resolve_target_dir, install_skill


def test_find_skill_source():
    source = find_skill_source()
    assert source.exists()
    assert (source / "SKILL.md").exists()
    assert (source / "templates").is_dir()


def test_resolve_target_dir_workspace():
    path_agents = resolve_target_dir(agent="agents")
    assert path_agents.name == "adapter-scaffolder"
    assert ".agents" in str(path_agents)

    path_claude = resolve_target_dir(agent="claude")
    assert ".claude" in str(path_claude)

    path_custom = resolve_target_dir(target_dir="custom/path")
    assert path_custom.name == "path"


def test_resolve_target_dir_global():
    path_global = resolve_target_dir(agent="agents", is_global=True)
    assert ".gemini" in str(path_global) or ".agents" in str(path_global)


def test_install_skill_execution(tmp_path: Path):
    target_dir = tmp_path / "my_skill_dir"
    installed = install_skill(target_dir=str(target_dir))

    assert installed.exists()
    assert (installed / "SKILL.md").exists()
    assert (installed / "templates" / "python_adapter.py").exists()

    # Testing overwrite protection
    with pytest.raises(FileExistsError):
        install_skill(target_dir=str(target_dir), force=False)

    # Force overwrite
    installed_again = install_skill(target_dir=str(target_dir), force=True)
    assert installed_again.exists()
