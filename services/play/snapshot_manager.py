"""剧目缓存快照管理工具。"""
from __future__ import annotations

import asyncio
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Dict, Iterator, Optional

from sqlmodel import Session, select

from ..db.connection import get_session
from ..db.models import Play, PlaySnapshot

_DEFAULT_TTL = int(os.getenv("PLAY_SNAPSHOT_TTL", "900"))
_BACKGROUND_LIMIT = int(os.getenv("SNAPSHOT_BACKGROUND_LIMIT", "4"))
_BACKGROUND_SEMAPHORE = asyncio.Semaphore(_BACKGROUND_LIMIT)


@contextmanager
def _session_scope(session: Optional[Session] = None) -> Iterator[Session]:
    if session is not None:
        yield session
    else:
        with get_session() as managed_session:
            yield managed_session


def rebuild_snapshot(
    play_id: int,
    *,
    city_norm: Optional[str] = None,
    payload: Optional[Dict[str, object]] = None,
    ttl_seconds: Optional[int] = None,
    session: Optional[Session] = None,
) -> PlaySnapshot:
    """根据最新聚合结果刷新剧目缓存快照。"""

    ttl_value = ttl_seconds or _DEFAULT_TTL
    with _session_scope(session) as current_session:
        play = current_session.get(Play, play_id)
        if play is None:
            raise ValueError(f"未找到剧目: {play_id}")

        statement = select(PlaySnapshot).where(
            PlaySnapshot.play_id == play_id,
            PlaySnapshot.is_deleted.is_(False),
        )
        snapshot = current_session.exec(statement).one_or_none()

        now = datetime.now(timezone.utc)
        effective_city = city_norm or play.default_city_norm
        if payload is None:
            payload = {
                "play_id": play_id,
                "name": play.name,
                "city_norm": effective_city,
                "generated_at": now.isoformat(),
                "tickets": [],
                "schedule": [],
                "cast": [],
                "summary": {},
            }

        if snapshot is None:
            snapshot = PlaySnapshot(
                play_id=play_id,
                city_norm=effective_city,
                payload=payload,
                ttl_seconds=ttl_value,
                last_success_at=now,
            )
            current_session.add(snapshot)
        else:
            snapshot.city_norm = effective_city
            snapshot.payload = payload
            snapshot.ttl_seconds = ttl_value
            snapshot.last_success_at = now
            current_session.add(snapshot)

        current_session.commit()
        current_session.refresh(snapshot)
        return snapshot


def _snapshot_is_stale(snapshot: PlaySnapshot, ttl_value: int) -> bool:
    if snapshot.last_success_at is None:
        return True
    last_success = snapshot.last_success_at
    if last_success.tzinfo is None:
        last_success = last_success.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - last_success
    return age.total_seconds() >= ttl_value


async def _async_rebuild(play_id: int, city_norm: Optional[str]) -> None:
    async with _BACKGROUND_SEMAPHORE:
        await asyncio.to_thread(rebuild_snapshot, play_id, city_norm=city_norm)


def _schedule_rebuild(
    play_id: int, city_norm: Optional[str], session: Optional[Session] = None
) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        rebuild_snapshot(play_id, city_norm=city_norm, session=session)
        return

    loop.create_task(_async_rebuild(play_id, city_norm))


def get_play_full(
    play_id: int,
    *,
    city_hint: Optional[str] = None,
    session: Optional[Session] = None,
) -> Dict[str, object]:
    """返回剧目的完整缓存数据并根据 TTL 判定是否需要刷新。"""

    ttl_value = _DEFAULT_TTL
    with _session_scope(session) as current_session:
        statement = select(PlaySnapshot).where(
            PlaySnapshot.play_id == play_id,
            PlaySnapshot.is_deleted.is_(False),
        )
        if city_hint:
            statement = statement.where(PlaySnapshot.city_norm == city_hint)
        snapshot = current_session.exec(statement).one_or_none()

        stale = True
        payload: Dict[str, object] = {}
        if snapshot is not None and snapshot.payload:
            ttl_value = snapshot.ttl_seconds or ttl_value
            stale = _snapshot_is_stale(snapshot, ttl_value)
            payload = dict(snapshot.payload)
        else:
            stale = True

        if stale:
            _schedule_rebuild(play_id, city_hint, current_session if session else None)

        return {
            "play_id": play_id,
            "city_norm": city_hint or (snapshot.city_norm if snapshot else None),
            "tickets": payload.get("tickets", []),
            "schedule": payload.get("schedule", []),
            "cast": payload.get("cast", []),
            "summary": payload.get("summary", {}),
            "stale": stale,
            "ttl_seconds": ttl_value,
            "last_success_at": snapshot.last_success_at if snapshot else None,
        }


__all__ = ["rebuild_snapshot", "get_play_full"]
