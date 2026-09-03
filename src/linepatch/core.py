"""The conservative, deterministic text-repair engine."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RepairResult:
    """A repaired document and an auditable count of the operations performed."""

    input_text: str
    text: str
    joined_lines: int
    dehyphenated_words: int
    normalized_artifacts: int

    @property
    def changed(self) -> bool:
        return self.input_text != self.text

    @property
    def change_count(self) -> int:
        return self.joined_lines + self.dehyphenated_words + self.normalized_artifacts


_LIST_RE = re.compile(r"^\s*(?:[-*+•]\s+|\d+[.)]\s+|[A-Za-z][.)]\s+)")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+\S")
_URL_OR_EMAIL_RE = re.compile(
    r"^(?:https?://\S+|www\.\S+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,})$",
    re.IGNORECASE,
)
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_TERMINAL = frozenset(".!?。！？")


def _normalize_artifacts(text: str) -> tuple[str, int]:
    """Normalize transport artifacts while leaving user formatting alone."""

    count = text.count("\r")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    for character in ("\u00a0", "\u202f"):
        occurrences = normalized.count(character)
        if occurrences:
            normalized = normalized.replace(character, " ")
            count += occurrences

    occurrences = normalized.count("\u00ad")
    if occurrences:
        normalized = normalized.replace("\u00ad", "")
        count += occurrences

    for character in ("\u200b", "\u200c", "\u200d", "\ufeff"):
        occurrences = normalized.count(character)
        if occurrences:
            normalized = normalized.replace(character, "")
            count += occurrences

    return normalized, count


def _is_structural(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if _FENCE_RE.match(line) or _LIST_RE.match(line) or _HEADING_RE.match(line):
        return True
    if stripped.startswith((">", "|")) or _URL_OR_EMAIL_RE.fullmatch(stripped):
        return True
    if len(stripped) >= 3 and set(stripped) <= set("-_*= "):
        return True
    return False


def _looks_like_title(line: str) -> bool:
    """Spot short title-case lines without rejecting ordinary prose."""

    stripped = line.strip()
    if len(stripped) > 72:
        return False
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", stripped)
    if not words or len(words) > 8:
        return False
    capitalized = sum(word[0].isupper() for word in words)
    return capitalized == len(words) and not line.rstrip().endswith(tuple(_TERMINAL))


def _can_join(previous: str, following: str) -> tuple[bool, bool]:
    """Return ``(can_join, remove_line_hyphen)`` for two nonblank lines."""

    if _is_structural(previous) or _is_structural(following):
        return False, False

    left = previous.rstrip()
    right = following.lstrip()
    if not left or not right or _looks_like_title(left) or _looks_like_title(right):
        return False, False

    if (
        left.endswith("-")
        and len(left) > 1
        and left[-2].isalnum()
        and right[0].islower()
    ):
        return True, True

    first = right[0]
    if left[-1] in _TERMINAL or (left[-1] == ":" and first.isupper()):
        return False, False
    if first.islower() or first.isdigit() or first in "([{\"'":
        return True, False
    if left[-1] in ",;—–/":
        return True, False

    # A PDF may capitalize the first word of a wrapped line. Require a
    # paragraph-shaped pair so a short label followed by a sentence stays put.
    if first.isupper() and len(left.split()) >= 3 and len(right.split()) >= 2:
        return True, False
    return False, False


def repair_text(text: str) -> RepairResult:
    """Repair high-confidence copy artifacts and return the proposed result."""

    normalized, normalized_artifacts = _normalize_artifacts(text)
    lines = normalized.split("\n")
    repaired: list[str] = []
    joined_lines = 0
    dehyphenated_words = 0
    in_fence = False
    index = 0

    while index < len(lines):
        current = lines[index]
        if _FENCE_RE.match(current):
            repaired.append(current)
            in_fence = not in_fence
            index += 1
            continue
        if in_fence or not current.strip():
            repaired.append(current)
            index += 1
            continue

        pieces = [current]
        tail = current
        joined_for_current = False
        while index + 1 < len(lines) and lines[index + 1].strip():
            can_join, remove_line_hyphen = _can_join(tail, lines[index + 1])
            if not can_join:
                break
            following = lines[index + 1].lstrip()
            if remove_line_hyphen:
                pieces[-1] = pieces[-1].rstrip()[:-1] + following
                dehyphenated_words += 1
            else:
                pieces[-1] = pieces[-1].rstrip()
                pieces.append(following)
            tail = following
            joined_for_current = True
            joined_lines += 1
            index += 1
        repaired.append(" ".join(pieces) if joined_for_current else current)
        index += 1

    output = "\n".join(repaired)
    return RepairResult(
        input_text=text,
        text=output,
        joined_lines=joined_lines,
        dehyphenated_words=dehyphenated_words,
        normalized_artifacts=normalized_artifacts,
    )
