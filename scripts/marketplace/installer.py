"""
Skill installer for marketplace.

Downloads skills from GitHub repositories using git sparse checkout
and installs them to the .marketplace directory.
"""

import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any


def fetch_skill_files(repository: str, path: str, ref: str) -> tuple[Path, Path]:
    """
    Fetch skill files from GitHub using sparse checkout.

    Args:
        repository: GitHub repository URL
        path: Subdirectory path within repo
        ref: Git reference

    Returns:
        Tuple of (skill_dir, temp_root) where:
        - skill_dir: Path to directory containing skill files
        - temp_root: Path to temporary directory (for cleanup)

    Raises:
        RuntimeError: If git operations fail
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="claude-skill-install-"))

    try:
        # Initialize git
        subprocess.run(
            ["git", "init"],
            cwd=tmpdir,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "remote", "add", "origin", repository],
            cwd=tmpdir,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "core.sparseCheckout", "true"],
            cwd=tmpdir,
            check=True,
            capture_output=True
        )

        # Configure sparse checkout
        sparse_file = tmpdir / ".git" / "info" / "sparse-checkout"
        sparse_file.parent.mkdir(parents=True, exist_ok=True)
        sparse_file.write_text(f"{path}/*\n")

        # Fetch
        subprocess.run(
            ["git", "fetch", "--depth=1", "origin", ref],
            cwd=tmpdir,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "checkout", ref],
            cwd=tmpdir,
            check=True,
            capture_output=True
        )

        return tmpdir / path, tmpdir

    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise RuntimeError(f"Failed to fetch skill from {repository}/{path}@{ref}: {e}")


def install_skill(
    skill_metadata: Dict[str, Any],
    marketplace_dir: Path,
    ref: str
) -> None:
    """
    Install skill to marketplace directory.

    Args:
        skill_metadata: Skill metadata (name, repository, etc.)
        marketplace_dir: Path to .marketplace directory
        ref: Git reference to install

    Raises:
        RuntimeError: If installation fails
    """
    name = skill_metadata["name"]
    repository = skill_metadata["repository"]

    # Fetch files
    temp_skill_dir, temp_root = fetch_skill_files(repository, name, ref)

    try:
        # Copy to marketplace
        install_dir = marketplace_dir / name
        if install_dir.exists():
            shutil.rmtree(install_dir)

        shutil.copytree(temp_skill_dir, install_dir)

    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_root, ignore_errors=True)
