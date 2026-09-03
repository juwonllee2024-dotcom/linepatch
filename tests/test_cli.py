from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from linepatch.cli import main


class CliTests(unittest.TestCase):
    def test_stdin_writes_only_repaired_text_to_stdout(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch("sys.stdin", io.StringIO("A wrapped\nline.\n")):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(["-"])

        self.assertEqual(0, exit_code)
        self.assertEqual("A wrapped line.\n", stdout.getvalue())
        self.assertIn("1 joined line", stderr.getvalue())

    def test_output_requires_an_explicit_destination_and_reports_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "messy.txt"
            destination = Path(directory) / "clean.txt"
            source.write_text("A wrapped\nline.\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main([str(source), "--output", str(destination)])

            self.assertEqual(0, exit_code)
            self.assertEqual(
                "A wrapped line.\n",
                destination.read_text(encoding="utf-8"),
            )
            self.assertIn("wrote", stdout.getvalue())

    def test_diff_is_reviewable_without_writing_a_file(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdin", io.StringIO("A wrapped\nline.\n")):
            with redirect_stdout(stdout):
                exit_code = main(["-", "--diff"])

        self.assertEqual(0, exit_code)
        self.assertIn("-A wrapped", stdout.getvalue())
        self.assertIn("+A wrapped line.", stdout.getvalue())

    def test_existing_output_is_not_overwritten_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "messy.txt"
            destination = Path(directory) / "clean.txt"
            source.write_text("A wrapped\nline.\n", encoding="utf-8")
            destination.write_text("keep me\n", encoding="utf-8")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main([str(source), "--output", str(destination)])

            self.assertEqual(2, exit_code)
            self.assertEqual("keep me\n", destination.read_text(encoding="utf-8"))
            self.assertIn("already exists", stderr.getvalue())

    def test_force_cannot_replace_a_hard_link_to_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "messy.txt"
            alias = Path(directory) / "alias.txt"
            source.write_text("A wrapped\nline.\n", encoding="utf-8")
            try:
                os.link(source, alias)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"hard links unavailable: {exc}")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main([str(source), "--output", str(alias), "--force"])

            self.assertEqual(2, exit_code)
            self.assertEqual("A wrapped\nline.\n", source.read_text(encoding="utf-8"))
            self.assertIn("same file", stderr.getvalue())

    def test_force_does_not_follow_an_output_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "messy.txt"
            target = Path(directory) / "target.txt"
            link = Path(directory) / "output.txt"
            source.write_text("A wrapped\nline.\n", encoding="utf-8")
            target.write_text("keep me\n", encoding="utf-8")
            try:
                os.symlink(target, link)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main([str(source), "--output", str(link), "--force"])

            self.assertEqual(2, exit_code)
            self.assertEqual("keep me\n", target.read_text(encoding="utf-8"))
            self.assertIn("link", stderr.getvalue())

    def test_terminal_output_escapes_control_sequences(self) -> None:
        class TtyBuffer(io.StringIO):
            def isatty(self) -> bool:
                return True

        stdout = TtyBuffer()
        stderr = TtyBuffer()
        with patch("sys.stdin", io.StringIO("safe\x1b]52;c;clipboard\a\n")):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(["-"])

        self.assertEqual(0, exit_code)
        self.assertNotIn("\x1b", stdout.getvalue())
        self.assertIn(r"\x1b", stdout.getvalue())

    def test_input_size_limit_applies_to_stdin(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch("sys.stdin", io.StringIO("12345")):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(["-", "--max-input-bytes", "4"])

        self.assertEqual(2, exit_code)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("exceeds", stderr.getvalue())

    def test_input_limit_cannot_be_raised_above_the_hard_cap(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                main(["-", "--max-input-bytes", str(64 * 1024 * 1024 + 1)])

        self.assertEqual(2, raised.exception.code)
        self.assertIn("must not exceed", stderr.getvalue())

    def test_force_replaces_regular_output_without_touching_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "messy.txt"
            destination = Path(directory) / "clean.txt"
            source.write_text("A wrapped\nline.\n", encoding="utf-8")
            destination.write_text("old\n", encoding="utf-8")

            exit_code = main([str(source), "--output", str(destination), "--force"])

            self.assertEqual(0, exit_code)
            self.assertEqual(
                "A wrapped line.\n", destination.read_text(encoding="utf-8")
            )
            self.assertEqual("A wrapped\nline.\n", source.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
