"""Hulaquan 插件入口，延迟加载主类以避免副作用。"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - 仅用于类型检查
    from .main import Hulaquan as _Hulaquan

__all__ = ["Hulaquan"]


def __getattr__(name: str):
    if name == "Hulaquan":
        from .main import Hulaquan as _Hulaquan

        return _Hulaquan
    raise AttributeError(name)
