"""Command-line interface for LinePatch."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import sys
import tempfile
import unicodedata
from collections.abc import Sequence
from pathlib import Path
from typing import BinaryIO, TextIO, cast

from .core import RepairResult, repair_text

VERSION = "0.1.0"
DEFAULT_MAX_INPUT_BYTES = 10 * 1024 * 1024
DEFAULT_MAX_LINES = 100_000
HARD_MAX_INPUT_BYTES = 64 * 1024 * 1024
HARD_MAX_LINES = 1_000_000
READ_CHUNK_BYTES = 64 * 1024


def _bounded_positive_int(value: str, maximum: int, label: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    if parsed > maximum:
        raise argparse.ArgumentTypeError(f"must not exceed {maximum} {label}")
    return parsed


def _input_bytes(value: str) -> int:
    return _bounded_positive_int(value, HARD_MAX_INPUT_BYTES, "bytes")


def _line_count(value: str) -> int:
    return _bounded_positive_int(value, HARD_MAX_LINES, "lines")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="linepatch",
        description="make copied PDF text readable before it enters your AI",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="UTF-8 text file, or - for stdin",
    )
    parser.add_argument(
        "--max-input-bytes",
        type=_input_bytes,
        default=DEFAULT_MAX_INPUT_BYTES,
        metavar="N",
        help=(
            "reject input larger than N UTF-8 bytes "
            "(default: 10485760; hard limit: 67108864)"
        ),
    )
    parser.add_argument(
        "--max-lines",
        type=_line_count,
        default=DEFAULT_MAX_LINES,
        metavar="N",
        help="reject input over N lines (default: 100000; hard cap: 1000000)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="write repaired text to this new destination; never overwrites input",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow replacing an existing output file (input is still protected)",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="print a unified diff for review instead of repaired text",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print a machine-readable report (and include repaired text)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="return 1 when a repair would be proposed",
    )
    parser.add_argument("--version", action="version", version=f"linepatch {VERSION}")
    return parser


def _read_binary(stream: BinaryIO, limit: int, label: str) -> str:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = stream.read(READ_CHUNK_BYTES)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise ValueError(f"{label} exceeds the {limit}-byte input limit")
        chunks.append(chunk)
    return b"".join(chunks).decode("utf-8")


def _read_text(stream: TextIO, limit: int, label: str) -> str:
    chunks: list[str] = []
    total = 0
    while True:
        chunk = stream.read(READ_CHUNK_BYTES)
        if not chunk:
            break
        total += len(chunk.encode("utf-8"))
        if total > limit:
            raise ValueError(f"{label} exceeds the {limit}-byte input limit")
        chunks.append(chunk)
    return "".join(chunks)


def _enforce_line_limit(text: str, limit: int, label: str) -> str:
    line_count = (
        text.count("\n")
        + text.count("\r")
        - text.count("\r\n")
        + (1 if text and not text.endswith(("\n", "\r")) else 0)
    )
    if line_count > limit:
        raise ValueError(f"{label} exceeds the {limit}-line input limit")
    return text


def _read_input(name: str, max_input_bytes: int, max_lines: int) -> str:
    if name == "-":
        binary_stream = getattr(sys.stdin, "buffer", None)
        if binary_stream is not None:
            text = _read_binary(cast(BinaryIO, binary_stream), max_input_bytes, "stdin")
        else:
            text = _read_text(cast(TextIO, sys.stdin), max_input_bytes, "stdin")
        return _enforce_line_limit(text, max_lines, "stdin")

    with Path(name).open("rb") as stream:
        text = _read_binary(stream, max_input_bytes, name)
    return _enforce_line_limit(text, max_lines, name)


def _label(count: int, singular: str, plural: str | None = None) -> str:
    return f"{count} {singular if count == 1 else plural or singular + 's'}"


def _summary(result: RepairResult) -> str:
    if not result.changed:
        return "no changes"
    parts: list[str] = []
    if result.joined_lines:
        parts.append(_label(result.joined_lines, "joined line"))
    if result.dehyphenated_words:
        parts.append(_label(result.dehyphenated_words, "dehyphenated word"))
    if result.normalized_artifacts:
        parts.append(_label(result.normalized_artifacts, "normalized artifact"))
    return ", ".join(parts)


def _same_file(first: Path, second: Path) -> bool:
    try:
        return os.path.samefile(first, second)
    except (FileNotFoundError, OSError):
        return first.resolve() == second.resolve()


def _is_link_or_reparse_point(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    except (FileNotFoundError, OSError):
        return False
    return bool(attributes & 0x400)


def _write_output(
    path: Path,
    content: str,
    *,
    force: bool,
    source: Path | None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if source is not None and _same_file(source, path):
        raise ValueError("output is the same file as input; source was not changed")
    if _is_link_or_reparse_point(path):
        raise ValueError("output cannot be a symlink or reparse point")

    if not force:
        try:
            with path.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
        except FileExistsError as exc:
            raise FileExistsError(
                f"output already exists: {path}; choose another path or pass --force"
            ) from exc
        return

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=".linepatch-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def _render_diff(result: RepairResult, source_name: str) -> str:
    diff = difflib.unified_diff(
        result.input_text.splitlines(keepends=True),
        result.text.splitlines(keepends=True),
        fromfile=source_name,
        tofile="linepatch (repaired)",
    )
    return "".join(diff)


def _render_json(result: RepairResult, source_name: str) -> str:
    payload = {
        "input": source_name,
        "changed": result.changed,
        "change_count": result.change_count,
        "joined_lines": result.joined_lines,
        "dehyphenated_words": result.dehyphenated_words,
        "normalized_artifacts": result.normalized_artifacts,
        "text": result.text,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _escape_terminal_controls(content: str) -> str:
    escaped: list[str] = []
    for character in content:
        if character in "\n\r\t" or unicodedata.category(character) not in {"Cc", "Cf"}:
            escaped.append(character)
            continue
        codepoint = ord(character)
        escaped.append(
            f"\\x{codepoint:02x}" if codepoint <= 0xFF else f"\\u{codepoint:04x}"
        )
    return "".join(escaped)


def _emit(stream: TextIO, content: str) -> None:
    if stream.isatty():
        content = _escape_terminal_controls(content)
    stream.write(content)


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(errors="backslashreplace")

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.diff and args.output is not None:
        parser.error("--diff previews changes; remove --output or use them separately")

    source_name = "stdin" if args.input == "-" else args.input
    try:
        input_path = None if args.input == "-" else Path(args.input)
        if args.output is not None and input_path is not None:
            if _same_file(input_path, args.output):
                raise ValueError(
                    "output is the same file as input; source was not changed"
                )
        result = repair_text(
            _read_input(args.input, args.max_input_bytes, args.max_lines)
        )
        if args.diff:
            _emit(sys.stdout, _render_diff(result, source_name))
        elif args.json:
            if args.output is not None:
                _write_output(
                    args.output,
                    result.text,
                    force=args.force,
                    source=input_path,
                )
                _emit(
                    sys.stdout, f"linepatch: wrote {args.output} ({_summary(result)})\n"
                )
            else:
                _emit(sys.stdout, _render_json(result, source_name))
        elif args.output is not None:
            _write_output(
                args.output,
                result.text,
                force=args.force,
                source=input_path,
            )
            _emit(sys.stdout, f"linepatch: wrote {args.output} ({_summary(result)})\n")
        else:
            _emit(sys.stdout, result.text)
            _emit(sys.stderr, f"linepatch: {_summary(result)}\n")
    except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
        _emit(sys.stderr, f"linepatch: error: {exc}\n")
        return 2

    return 1 if args.check and result.changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
