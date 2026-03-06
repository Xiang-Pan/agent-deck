"""Proof-of-concept: pexpect smoke tests for Agent Deck TUI.

These tests launch the real binary and interact with it the way a human
would — pressing keys and asserting on visible terminal output.
"""

import pexpect
import pytest


class TestHelpFlag:
    """Sanity: --help exits cleanly and prints usage info."""

    def test_help_prints_usage(self, spawn_deck):
        child = spawn_deck("--help")
        child.expect("Usage")
        child.expect(pexpect.EOF)
        child.close()
        assert child.exitstatus == 0


class TestVersionFlag:
    """Sanity: --version exits cleanly."""

    def test_version_output(self, spawn_deck):
        child = spawn_deck("version")
        child.expect(pexpect.EOF)
        child.close()
        assert child.exitstatus == 0


class TestTUILaunch:
    """Launch the TUI and perform basic smoke interactions."""

    def test_tui_renders_initial_screen(self, spawn_deck):
        """TUI should render without crashing and show the home screen."""
        child = spawn_deck()
        # The home screen should contain some recognizable text
        # (e.g. "Agent Deck", session list, or the help bar).
        idx = child.expect(
            [r"[Aa]gent\s*[Dd]eck", r"No sessions", r"Press .* to", pexpect.TIMEOUT],
            timeout=5,
        )
        assert idx != 3, f"TUI did not render expected content within timeout.\nBuffer: {child.before}"

    def test_help_key_toggles_help(self, spawn_deck):
        """Pressing '?' should open the help overlay."""
        child = spawn_deck()
        # Wait for the initial render.
        child.expect(
            [r"[Aa]gent\s*[Dd]eck", r"No sessions", r"Press .* to", pexpect.TIMEOUT],
            timeout=5,
        )
        child.send("?")
        idx = child.expect([r"[Hh]elp", r"[Kk]eybind", pexpect.TIMEOUT], timeout=3)
        assert idx != 2, "Help overlay did not appear after pressing '?'"

    def test_quit_key_exits(self, spawn_deck):
        """Pressing 'q' on the home screen should exit cleanly."""
        child = spawn_deck()
        child.expect(
            [r"[Aa]gent\s*[Dd]eck", r"No sessions", r"Press .* to", pexpect.TIMEOUT],
            timeout=5,
        )
        child.send("q")
        child.expect(pexpect.EOF, timeout=5)
        child.close()
        assert child.exitstatus == 0


class TestNewSessionDialog:
    """Open the new-session dialog and verify basic field navigation."""

    def test_open_new_session_dialog(self, spawn_deck):
        """Pressing 'n' should open the new-session dialog."""
        child = spawn_deck()
        child.expect(
            [r"[Aa]gent\s*[Dd]eck", r"No sessions", r"Press .* to", pexpect.TIMEOUT],
            timeout=5,
        )
        child.send("n")
        idx = child.expect(
            [r"[Nn]ew [Ss]ession", r"[Nn]ame", r"[Pp]ath", pexpect.TIMEOUT],
            timeout=3,
        )
        assert idx != 3, "New-session dialog did not open after pressing 'n'"

    def test_escape_closes_dialog(self, spawn_deck):
        """Escape should close the new-session dialog without creating a session."""
        child = spawn_deck()
        child.expect(
            [r"[Aa]gent\s*[Dd]eck", r"No sessions", r"Press .* to", pexpect.TIMEOUT],
            timeout=5,
        )
        child.send("n")
        child.expect(
            [r"[Nn]ew [Ss]ession", r"[Nn]ame", r"[Pp]ath", pexpect.TIMEOUT],
            timeout=3,
        )
        child.send("\x1b")  # ESC
        # After closing the dialog we should be back at the home screen.
        idx = child.expect(
            [r"[Aa]gent\s*[Dd]eck", r"No sessions", r"Press .* to", pexpect.TIMEOUT],
            timeout=3,
        )
        assert idx != 3, "Dialog did not close after pressing Escape"
