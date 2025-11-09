"""自定义 unittest 发现逻辑，默认聚焦 tests 目录。"""
from __future__ import annotations

import unittest

_ORIGINAL_DISCOVER = unittest.TestLoader.discover


def _patched_discover(self, start_dir=None, pattern="test*.py", top_level_dir=None):
    """如果未显式指定目录，则默认只扫描 tests/。"""

    actual_start_dir = start_dir or "tests"
    if actual_start_dir in {".", ""}:
        actual_start_dir = "tests"
    return _ORIGINAL_DISCOVER(self, actual_start_dir, pattern, top_level_dir)


unittest.TestLoader.discover = _patched_discover  # type: ignore[assignment]
