"""Shared fixtures for pexpect-based TUI tests."""

import os
import shutil
import subprocess
import tempfile

import pexpect
import pytest

BINARY_NAME = "agent-deck"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")
BINARY_PATH = os.path.join(BUILD_DIR, BINARY_NAME)

# Minimum terminal size required by the TUI.
COLS = 120
ROWS = 40


def _ensure_binary():
    """Build the binary if it doesn't exist or is stale."""
    if not os.path.isfile(BINARY_PATH):
        subprocess.check_call(["make", "build"], cwd=PROJECT_ROOT)


@pytest.fixture(scope="session", autouse=True)
def build_binary():
    """Build the binary once per test-session."""
    _ensure_binary()


@pytest.fixture()
def spawn_deck(tmp_path):
    """Spawn agent-deck in a pseudo-terminal via pexpect.

    Yields a factory function so individual tests can pass extra CLI args.
    The child process is killed on teardown.

    Usage::

        def test_something(spawn_deck):
            child = spawn_deck()            # launches `agent-deck`
            child = spawn_deck("--help")    # launches `agent-deck --help`
    """
    children: list[pexpect.spawn] = []

    def _factory(extra_args: str = "", env_overrides: dict | None = None):
        env = os.environ.copy()
        # Isolate test runs from the user's real profile / data.
        env["AGENTDECK_PROFILE"] = "_tui_test"
        # Provide a throwaway home so config files don't collide.
        env["HOME"] = str(tmp_path)
        if env_overrides:
            env.update(env_overrides)

        cmd = f"{BINARY_PATH} {extra_args}".strip()
        child = pexpect.spawn(
            cmd,
            encoding="utf-8",
            timeout=10,
            dimensions=(ROWS, COLS),
            env=env,
        )
        children.append(child)
        return child

    yield _factory

    for child in children:
        if child.isalive():
            child.terminate(force=True)
