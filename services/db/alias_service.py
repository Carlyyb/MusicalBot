"""剧目别名与来源链接的数据服务层。"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Dict, Iterator, List, Optional, Sequence, Tuple, Union

from sqlmodel import Session, select

from ..search.normalize import normalize_city, normalize_text
from .connection import get_session
from .models import Play, WorkAlias, WorkSourceLink

AliasIdentifier = Union[int, str]


@contextmanager
def _session_scope(session: Optional[Session] = None) -> Iterator[Session]:
    """统一处理可选会话的上下文。"""

    if session is not None:
        yield session
    else:
        with get_session() as managed_session:
            yield managed_session


def _build_alias_payload(
    play: Play,
    alias: WorkAlias,
    *,
    city_norm: Optional[str] = None,
) -> Dict[str, Union[str, int]]:
    return {
        "play_id": play.id,
        "play_name": play.name,
        "alias": alias.alias,
        "source": alias.source,
        "city_norm": city_norm or play.default_city_norm,
        "weight": alias.weight,
        "no_response_count": alias.no_response_count,
    }


def add_alias(
    play_id: int,
    alias: str,
    *,
    source: str = "manual",
    weight: int = 0,
    session: Optional[Session] = None,
) -> WorkAlias:
    """为剧目添加别名，自动处理标准化字段。"""

    alias_norm = normalize_text(alias)
    with _session_scope(session) as current_session:
        record = WorkAlias(
            work_id=play_id,
            alias=alias,
            alias_norm=alias_norm,
            source=source,
            weight=weight,
            last_used_at=datetime.now(timezone.utc),
        )
        current_session.add(record)
        current_session.commit()
        current_session.refresh(record)
        return record


def find_play_by_alias_or_name(
    q_title_norm: str,
    q_city_norm: Optional[str] = None,
    *,
    session: Optional[Session] = None,
) -> Union[int, List[Dict[str, Union[str, int]]]]:
    """通过别名或名称查找剧目。"""

    alias_norm = normalize_text(q_title_norm)
    city_norm = normalize_city(q_city_norm)

    with _session_scope(session) as current_session:
        alias_stmt = (
            select(WorkAlias, Play)
            .join(Play, Play.id == WorkAlias.work_id)
            .where(
                WorkAlias.alias_norm == alias_norm,
                WorkAlias.is_deleted.is_(False),
                Play.is_deleted.is_(False),
            )
        )
        alias_rows: Sequence[Tuple[WorkAlias, Play]] = current_session.exec(alias_stmt).all()

        for alias_record, _ in alias_rows:
            alias_record.last_used_at = datetime.now(timezone.utc)
            current_session.add(alias_record)

        play_stmt = select(Play).where(
            Play.name_norm == alias_norm,
            Play.is_deleted.is_(False),
        )
        play_rows: Sequence[Play] = current_session.exec(play_stmt).all()

        candidates: Dict[int, Dict[str, Union[str, int]]] = {}

        for alias_record, play in alias_rows:
            payload = _build_alias_payload(play, alias_record, city_norm=city_norm)
            candidates[play.id] = payload

        for play in play_rows:
            payload = {
                "play_id": play.id,
                "play_name": play.name,
                "alias": play.name,
                "source": "official",
                "city_norm": city_norm or play.default_city_norm,
                "weight": 0,
                "no_response_count": 0,
            }
            candidates.setdefault(play.id, payload)

        current_session.commit()

        if not candidates:
            return []

        if len(candidates) == 1:
            return next(iter(candidates.keys()))

        return list(candidates.values())


def record_no_response(
    alias_or_play: AliasIdentifier,
    *,
    session: Optional[Session] = None,
) -> int:
    """记录别名未命中的次数。"""

    with _session_scope(session) as current_session:
        now = datetime.now(timezone.utc)
        if isinstance(alias_or_play, int):
            stmt = select(WorkAlias).where(
                WorkAlias.work_id == alias_or_play,
                WorkAlias.is_deleted.is_(False),
            )
        else:
            alias_norm = normalize_text(str(alias_or_play))
            stmt = select(WorkAlias).where(
                WorkAlias.alias_norm == alias_norm,
                WorkAlias.is_deleted.is_(False),
            )

        rows = list(current_session.exec(stmt).all())
        for record in rows:
            record.no_response_count += 1
            record.last_used_at = now
            current_session.add(record)

        current_session.commit()
        return len(rows)


def link_source(
    play_id: int,
    source_kind: str,
    source_id: str,
    *,
    title_at_source: Optional[str] = None,
    city_hint: Optional[str] = None,
    confidence: float = 1.0,
    payload_hash: Optional[str] = None,
    last_sync_at: Optional[datetime] = None,
    session: Optional[Session] = None,
) -> WorkSourceLink:
    """更新或插入剧目来源链接。"""

    with _session_scope(session) as current_session:
        stmt = select(WorkSourceLink).where(
            WorkSourceLink.work_id == play_id,
            WorkSourceLink.source == source_kind,
            WorkSourceLink.source_id == source_id,
            WorkSourceLink.is_deleted.is_(False),
        )
        link = current_session.exec(stmt).one_or_none()

        if link is None:
            link = WorkSourceLink(
                work_id=play_id,
                source=source_kind,
                source_id=source_id,
                title_at_source=title_at_source,
                city_hint=city_hint,
                confidence=confidence,
                payload_hash=payload_hash,
                last_sync_at=last_sync_at or datetime.now(timezone.utc),
            )
        else:
            link.title_at_source = title_at_source or link.title_at_source
            link.city_hint = city_hint or link.city_hint
            link.confidence = confidence
            link.payload_hash = payload_hash or link.payload_hash
            link.last_sync_at = last_sync_at or datetime.now(timezone.utc)

        current_session.add(link)
        current_session.commit()
        current_session.refresh(link)
        return link


def get_aliases_for_work(
    work_id: int,
    *,
    session: Optional[Session] = None,
) -> List[WorkAlias]:
    """兼容旧接口，返回指定剧目的全部别名。"""

    with _session_scope(session) as current_session:
        stmt = select(WorkAlias).where(
            WorkAlias.work_id == work_id,
            WorkAlias.is_deleted.is_(False),
        )
        return list(current_session.exec(stmt).all())


__all__ = [
    "add_alias",
    "find_play_by_alias_or_name",
    "record_no_response",
    "link_source",
    "get_aliases_for_work",
]
