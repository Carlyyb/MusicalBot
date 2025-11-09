"""通用的文本规范化工具。"""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

# 去除常见中英文标点及 ^._- 等符号
_REMOVE_CHARS = "《》" + "\"'`~!@#$%^&*()[]{}:;?,./\\|_-"
_TRANSLATION_TABLE = str.maketrans({ch: " " for ch in _REMOVE_CHARS})
_WHITESPACE_RE = re.compile(r"\s+")


@lru_cache(maxsize=1024)
def normalize_text(value: str | None) -> str:
    """统一大小写、全半角并移除多余符号。"""

    if not value:
        return ""
    text = unicodedata.normalize("NFKC", value)
    text = text.translate(_TRANSLATION_TABLE)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip().lower()


def normalize_city(value: str | None) -> str:
    """城市名使用相同的文本规范化规则。"""

    return normalize_text(value)


__all__ = ["normalize_text", "normalize_city"]
