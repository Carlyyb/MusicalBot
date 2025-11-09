"""兼容旧 HulaquanDataManager 的服务入口，内部已转调 DB/Service。"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Iterator, Optional, Union

from sqlmodel import Session, select

from ..db.connection import get_session
from ..db.models import PlaySnapshot, WorkSourceLink
from ..play.snapshot_manager import get_play_full
from ..search.normalize import normalize_city

Identifier = Union[int, str]


@contextmanager
def _session_scope(session: Optional[Session] = None) -> Iterator[Session]:
    if session is not None:
        yield session
    else:
        with get_session() as managed_session:
            yield managed_session


def _resolve_play_id(identifier: Identifier, session: Session) -> Optional[int]:
    if isinstance(identifier, int):
        return identifier

    stmt = select(WorkSourceLink).where(
        WorkSourceLink.source_id == str(identifier),
        WorkSourceLink.is_deleted.is_(False),
    )
    link = session.exec(stmt).first()
    return link.work_id if link else None


def get_event_tickets(
    identifier: Identifier,
    *,
    city_hint: Optional[str] = None,
    session: Optional[Session] = None,
) -> Optional[Dict[str, object]]:
    """返回缓存的剧目信息，兼容旧管理器。"""

    city_norm = normalize_city(city_hint)
    with _session_scope(session) as current_session:
        play_id = _resolve_play_id(identifier, current_session)
        if play_id is None:
            return None

        snapshot_stmt = select(PlaySnapshot).where(
            PlaySnapshot.play_id == play_id,
            PlaySnapshot.is_deleted.is_(False),
        )
        snapshot = current_session.exec(snapshot_stmt).one_or_none()
        data = get_play_full(play_id, city_hint=city_norm)
        return {
            "play_id": play_id,
            "snapshot": snapshot.payload if snapshot and snapshot.payload else {},
            "latest": data,
        }


__all__ = ["get_event_tickets"]
