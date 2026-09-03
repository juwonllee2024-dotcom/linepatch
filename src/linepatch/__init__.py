"""Repair copied prose without silently rewriting the source."""

from .core import RepairResult, repair_text

__all__ = ["RepairResult", "repair_text"]
__version__ = "0.1.0"
