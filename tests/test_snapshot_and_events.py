"""剧目快照与 HLQ 事件流的单元测试。"""
from __future__ import annotations

import asyncio
import unittest
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, SQLModel, create_engine, select

from services.hulaquan.hlq_polling import HLQPollingService
from services.play.snapshot_manager import get_play_full, rebuild_snapshot
from services.db.models import Play, PlaySnapshot


class SnapshotCase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            echo=False,
        )
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        play = Play(name="剧目B", name_norm="剧目b")
        self.session.add(play)
        self.session.commit()
        self.session.refresh(play)
        self.play_id = play.id

    def tearDown(self) -> None:
        self.session.close()

    def test_get_play_full_and_ttl(self) -> None:
        snapshot = rebuild_snapshot(self.play_id, session=self.session)
        data = get_play_full(self.play_id, session=self.session)
        self.assertFalse(data["stale"])

        expired_at = datetime.now(timezone.utc) - timedelta(
            seconds=snapshot.ttl_seconds + 1
        )
        snapshot.last_success_at = expired_at
        self.session.add(snapshot)
        self.session.commit()

        data = get_play_full(self.play_id, session=self.session)
        self.assertTrue(data["stale"])
        refreshed = self.session.exec(
            select(PlaySnapshot).where(PlaySnapshot.play_id == self.play_id)
        ).one()
        refreshed_time = refreshed.last_success_at
        if refreshed_time.tzinfo is None:
            refreshed_time = refreshed_time.replace(tzinfo=timezone.utc)
        expired_time = expired_at
        if expired_time.tzinfo is None:
            expired_time = expired_time.replace(tzinfo=timezone.utc)
        self.assertGreater(refreshed_time, expired_time)

    def test_hlq_polling_emits_on_change(self) -> None:
        events: list = []

        async def fake_fetch() -> list:
            return [
                {
                    "play_id": self.play_id,
                    "city_norm": "上海",
                    "snapshot": {"tickets": [1]},
                    "payload_hash": "hash",
                }
            ]

        async def recorder(event) -> None:
            events.append(event)

        service = HLQPollingService(fake_fetch, on_update=recorder, processing_limit=1)

        async def scenario() -> None:
            await service.run_once()
            await service.run_once()

        asyncio.run(scenario())
        self.assertEqual(len(events), 1)

        async def fake_fetch_changed() -> list:
            return [
                {
                    "play_id": self.play_id,
                    "city_norm": "上海",
                    "snapshot": {"tickets": [1, 2]},
                    "payload_hash": "hash2",
                }
            ]

        service = HLQPollingService(fake_fetch_changed, on_update=recorder, processing_limit=1)

        asyncio.run(service.run_once())
        self.assertEqual(len(events), 2)


if __name__ == "__main__":  # pragma: no cover - 调试入口
    unittest.main()
