"""Hulaquan 轮询服务，负责拉取更新并触发事件。"""
from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Awaitable
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Sequence, Tuple

from ..db.health_check import network_logger
from ..play.snapshot_manager import rebuild_snapshot
from ..search.normalize import normalize_city

UpdatePayload = Dict[str, Any]
FetchCallable = Callable[[], Awaitable[Sequence[UpdatePayload]] | Sequence[UpdatePayload]]
Callback = Callable[["EventHLQUpdated"], Awaitable[None] | None]


@dataclass(slots=True)
class EventHLQUpdated:
    """HLQ 数据变更事件。"""

    play_id: int
    city_norm: Optional[str]
    payload: UpdatePayload
    payload_hash: str


class HLQPollingService:
    """轮询 HLQ 接口并在有变更时触发回调。"""

    def __init__(
        self,
        fetcher: FetchCallable,
        *,
        on_update: Optional[Callback] = None,
        processing_limit: Optional[int] = None,
    ) -> None:
        self._fetcher = fetcher
        self._on_update = on_update or self._default_on_update
        self._limit = processing_limit or int(os.getenv("HLQ_PROCESSING_LIMIT", "8"))
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._task: Optional[asyncio.Task[None]] = None
        self._stopped = asyncio.Event()
        self._last_hashes: Dict[Tuple[int, Optional[str]], str] = {}
        self._failure_count = 0

    async def _default_on_update(self, event: EventHLQUpdated) -> None:
        await asyncio.to_thread(
            rebuild_snapshot,
            event.play_id,
            city_norm=event.city_norm,
            payload=event.payload.get("snapshot"),
        )

    async def _call_fetcher(self) -> Sequence[UpdatePayload]:
        result = self._fetcher()
        if asyncio.iscoroutine(result) or isinstance(result, Awaitable):
            return await result  # type: ignore[return-value]
        return result  # type: ignore[return-value]

    def _interval(self) -> float:
        if self._failure_count <= 0:
            return 15.0
        if self._failure_count == 1:
            return 30.0
        return 90.0

    async def _emit(self, event: EventHLQUpdated) -> None:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._limit)

        async with self._semaphore:
            try:
                result = self._on_update(event)
                if asyncio.iscoroutine(result) or isinstance(result, Awaitable):
                    await result  # type: ignore[func-returns-value]
            except Exception:  # noqa: BLE001
                network_logger.exception(
                    "HLQ 更新回调执行失败",
                    extra={
                        "actor": "hlq",
                        "cmd": "emit",
                        "endpoint": "hlq",  # 兼容日志格式
                        "ok": False,
                    },
                )

    def _hash_payload(self, payload: UpdatePayload) -> str:
        if "payload_hash" in payload and payload["payload_hash"]:
            return str(payload["payload_hash"])
        return json.dumps(payload, sort_keys=True, ensure_ascii=False)

    async def _run_once(self) -> None:
        try:
            updates = await self._call_fetcher()
        except Exception:  # noqa: BLE001
            self._failure_count = min(self._failure_count + 1, 3)
            network_logger.exception(
                "HLQ 拉取失败",
                extra={
                    "actor": "hlq",
                    "cmd": "poll",
                    "endpoint": "hlq",
                    "ok": False,
                    "retry_count": self._failure_count,
                },
            )
            return

        self._failure_count = 0
        for item in updates:
            play_id = int(item.get("play_id"))
            city_norm = normalize_city(item.get("city_norm")) or None
            payload_hash = self._hash_payload(item)
            cache_key = (play_id, city_norm)
            if self._last_hashes.get(cache_key) == payload_hash:
                continue
            self._last_hashes[cache_key] = payload_hash
            event = EventHLQUpdated(
                play_id=play_id,
                city_norm=city_norm,
                payload=item,
                payload_hash=payload_hash,
            )
            await self._emit(event)

    async def _loop(self) -> None:
        self._stopped.clear()
        try:
            while not self._stopped.is_set():
                await self._run_once()
                await asyncio.sleep(self._interval())
        finally:
            self._task = None

    def start(self) -> None:
        if self._task is not None:
            return
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._loop())

    async def stop(self) -> None:
        self._stopped.set()
        if self._task is not None:
            await self._task
            self._task = None

    async def run_once(self) -> None:
        await self._run_once()


__all__ = ["HLQPollingService", "EventHLQUpdated"]
