"""兼容旧 JSON AliasManager 的服务入口，内部已转调 DB/Service。"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Iterator, Optional, Union

from sqlmodel import Session

from ..db.alias_service import (
    add_alias as _add_alias,
    find_play_by_alias_or_name,
    record_no_response as _record_no_response,
)
from ..db.connection import get_session


@contextmanager
def _session_scope(session: Optional[Session] = None) -> Iterator[Session]:
    if session is not None:
        yield session
    else:
        with get_session() as managed_session:
            yield managed_session


def add_alias(
    play_id: int,
    alias: str,
    *,
    source: str = "manual",
    weight: int = 0,
    session: Optional[Session] = None,
) -> Dict[str, Union[str, int]]:
    """写入别名并返回结构化结果。"""

    record = _add_alias(play_id, alias, source=source, weight=weight, session=session)
    return {
        "id": record.id,
        "alias": record.alias,
        "alias_norm": record.alias_norm,
        "weight": record.weight,
        "source": record.source,
    }


def find_by_alias(
    title: str,
    *,
    city_hint: Optional[str] = None,
    session: Optional[Session] = None,
) -> Dict[str, object]:
    """根据别名查询剧目，返回兼容旧逻辑的结果。"""

    result = find_play_by_alias_or_name(title, city_hint, session=session)
    if isinstance(result, int):
        return {"play_id": result, "candidates": []}
    return {"play_id": None, "candidates": result}


def record_no_response(
    alias_or_play: Union[int, str],
    *,
    session: Optional[Session] = None,
) -> int:
    """记录别名响应失败。"""

    return _record_no_response(alias_or_play, session=session)


__all__ = ["add_alias", "find_by_alias", "record_no_response"]
