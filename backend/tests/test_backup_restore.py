"""Backup/restore integration — requires Docker."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = REPO_ROOT / "docker-compose.backup-test.yml"
PASSPHRASE = "test-backup-passphrase-minimum-32-chars"


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def _compose(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    cmd = ["docker", "compose", "-f", str(COMPOSE_FILE), *args]
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
        env=merged,
    )


def _compose_run_backup(command: str, *, passphrase: str) -> subprocess.CompletedProcess[str]:
    return _compose(
        "run",
        "--rm",
        "-e",
        f"BACKUP_ENCRYPTION_PASSPHRASE={passphrase}",
        "-e",
        "ENVIRONMENT=production",
        "backup",
        command,
    )


@pytest.mark.docker
@pytest.mark.integration
@pytest.mark.skipif(not _docker_available(), reason="Docker not available")
def test_backup_restore_integration() -> None:
    """Backup → restore-test against ephemeral Compose stack (mirrors make backup-integration-test)."""
    _compose("down", "-v", "--remove-orphans")

    try:
        up = _compose("up", "-d", "postgres", "--wait")
        if up.returncode != 0:
            pytest.fail(f"postgres up failed\n{up.stdout}\n{up.stderr}")

        backup = _compose_run_backup("backup", passphrase=PASSPHRASE)
        if backup.returncode != 0:
            pytest.fail(f"backup failed\n{backup.stdout}\n{backup.stderr}")

        restore_test = _compose_run_backup("restore-test", passphrase=PASSPHRASE)
        if restore_test.returncode != 0:
            pytest.fail(f"restore-test failed\n{restore_test.stdout}\n{restore_test.stderr}")
    finally:
        _compose("down", "-v", "--remove-orphans")
