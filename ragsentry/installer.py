from __future__ import annotations

import os
import sys
import shutil
from pathlib import Path


def find_skill_source() -> Path:
    """Locate the source adapter-scaffolder skill directory."""
    package_dir = Path(__file__).resolve().parent

    # 1. Check inside package (pip-installed package data: site-packages/ragsentry/skills/adapter-scaffolder)
    pkg_skills = package_dir / "skills" / "adapter-scaffolder"
    if pkg_skills.exists() and (pkg_skills / "SKILL.md").exists():
        return pkg_skills

    # 2. Check relative to package root (repository / dev source)
    root_skills = package_dir.parent / "skills" / "adapter-scaffolder"
    if root_skills.exists() and (root_skills / "SKILL.md").exists():
        return root_skills

    # 3. Check site-packages or sys.prefix
    sys_prefix_skills = Path(sys.prefix) / "skills" / "adapter-scaffolder"
    if sys_prefix_skills.exists() and (sys_prefix_skills / "SKILL.md").exists():
        return sys_prefix_skills

    # 4. Check current working directory
    cwd_skills = Path.cwd() / "skills" / "adapter-scaffolder"
    if cwd_skills.exists() and (cwd_skills / "SKILL.md").exists():
        return cwd_skills

    raise FileNotFoundError(
        "Could not locate the 'adapter-scaffolder' skill source directory. "
        "Ensure RagSentry is properly installed with skill assets."
    )


def resolve_target_dir(
    agent: str = "agents",
    target_dir: str | None = None,
    is_global: bool = False,
) -> Path:
    """Determine destination path for installing the skill."""
    if target_dir:
        return Path(target_dir).resolve()

    agent_key = agent.lower().strip()

    if is_global:
        home = Path.home()
        if agent_key in ("claude",):
            return home / ".claude" / "skills" / "adapter-scaffolder"
        elif agent_key in ("cursor",):
            return home / ".cursor" / "skills" / "adapter-scaffolder"
        elif agent_key in ("windsurf",):
            return home / ".windsurfrules" / "adapter-scaffolder"
        else:
            # Default global path for Antigravity / Gemini / AGY / Standard agents
            return home / ".gemini" / "config" / "skills" / "adapter-scaffolder"
    else:
        if agent_key in ("claude",):
            return Path(".claude/skills/adapter-scaffolder").resolve()
        elif agent_key in ("cursor",):
            return Path(".cursor/skills/adapter-scaffolder").resolve()
        elif agent_key in ("windsurf",):
            return Path(".windsurfrules/adapter-scaffolder").resolve()
        else:
            # Default workspace path for Antigravity / AGY / Standard agents (.agents/skills/)
            return Path(".agents/skills/adapter-scaffolder").resolve()


def install_skill(
    agent: str = "agents",
    target_dir: str | None = None,
    is_global: bool = False,
    force: bool = False,
) -> Path:
    """Copy the adapter-scaffolder skill to the specified target directory."""
    source_dir = find_skill_source()
    destination = resolve_target_dir(agent=agent, target_dir=target_dir, is_global=is_global)

    if destination.exists() and not force:
        # Check if files exist
        if (destination / "SKILL.md").exists():
            raise FileExistsError(
                f"Skill already exists at '{destination}'. Use --force to overwrite."
            )

    destination.mkdir(parents=True, exist_ok=True)

    # Copy SKILL.md
    shutil.copy2(source_dir / "SKILL.md", destination / "SKILL.md")

    # Copy templates directory if present
    templates_src = source_dir / "templates"
    if templates_src.exists():
        templates_dest = destination / "templates"
        if templates_dest.exists():
            shutil.rmtree(templates_dest)
        shutil.copytree(templates_src, templates_dest)

    return destination
