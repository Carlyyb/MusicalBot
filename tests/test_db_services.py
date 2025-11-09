"""数据库服务层与剧目快照的单元测试。"""
from __future__ import annotations

import os
import unittest

from sqlmodel import Session, SQLModel, create_engine

from services.db.models import Group, Play, PlaySnapshot, Subscription, User
from services.db.group_service import create_group, get_groups_for_user
from services.db.init import init_db
from services.db.subscription_service import add_subscription, list_subscriptions
from services.db.models import SubscriptionTargetKind
from services.db.user_service import add_user, get_user_by_id, update_user_activity
from services.play.snapshot_manager import rebuild_snapshot


class DatabaseTestCase(unittest.TestCase):
    """为每个测试提供独立的内存数据库。"""

    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def tearDown(self) -> None:
        self.session.close()


class TestInitDb(DatabaseTestCase):
    """验证初始化脚本能够正确返回已创建的表。"""

    def test_init_db_returns_tables(self) -> None:
        tables = init_db(engine=self.engine, verbose=False)
        self.assertIn("users", tables)
        self.assertIn("subscriptions", tables)
        self.assertIn("play_snapshots", tables)


class TestUserService(DatabaseTestCase):
    """用户服务的基础增删改查验证。"""

    def test_user_crud_flow(self) -> None:
        created = add_user("123", nickname="测试用户", session=self.session)
        self.assertEqual(created.user_id, "123")
        self.assertEqual(created.nickname, "测试用户")

        fetched = get_user_by_id("123", session=self.session)
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertTrue(fetched.active)

        updated = update_user_activity("123", False, session=self.session)
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertFalse(updated.active)


class TestSubscriptionService(DatabaseTestCase):
    """订阅服务的基础功能验证。"""

    def setUp(self) -> None:
        super().setUp()
        add_user("456", nickname="订阅用户", session=self.session)

    def test_add_and_list_subscriptions(self) -> None:
        subscription_id = add_subscription(
            "456",
            SubscriptionTargetKind.PLAY,
            {"name": "音乐剧"},
            session=self.session,
        )
        self.assertIsInstance(subscription_id, int)

        bundles = list_subscriptions("456", session=self.session)
        self.assertEqual(len(bundles), 1)
        self.assertEqual(bundles[0]["subscription"].id, subscription_id)


class TestGroupService(DatabaseTestCase):
    """群组服务的基础功能验证。"""

    def test_create_and_list_groups(self) -> None:
        create_group("888", name="测试群", session=self.session)
        groups = get_groups_for_user("任意用户", session=self.session)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].group_id, "888")


class TestSnapshotManager(DatabaseTestCase):
    """剧目快照重建逻辑验证。"""

    def setUp(self) -> None:
        super().setUp()
        play = Play(name="剧目A", name_norm="jumu-a")
        self.session.add(play)
        self.session.commit()
        self.session.refresh(play)
        self.play_id = play.id

    def test_rebuild_snapshot_creates_record(self) -> None:
        snapshot = rebuild_snapshot(self.play_id, session=self.session)
        self.assertIsNotNone(snapshot.id)
        self.assertEqual(snapshot.play_id, self.play_id)
        self.assertIsInstance(snapshot.payload, dict)
        self.assertIn("generated_at", snapshot.payload)

    def test_rebuild_snapshot_updates_existing(self) -> None:
        first = rebuild_snapshot(self.play_id, session=self.session)
        updated_payload = {"play_id": self.play_id, "updated": True}
        second = rebuild_snapshot(
            self.play_id,
            payload=updated_payload,
            ttl_seconds=120,
            session=self.session,
        )
        self.assertEqual(first.id, second.id)
        self.assertEqual(second.payload["updated"], True)
        self.assertEqual(second.ttl_seconds, 120)


class TestHealthCheck(unittest.TestCase):
    """NapCat 健康检查脚本的默认实现验证。"""

    def tearDown(self) -> None:
        if "NAPCAT_SIMULATED_STATUS" in os.environ:
            del os.environ["NAPCAT_SIMULATED_STATUS"]

    def test_default_health_check_success(self) -> None:
        os.environ["NAPCAT_SIMULATED_STATUS"] = "online"
        from services.db.health_check import check_napcat_health

        self.assertTrue(check_napcat_health())

    def test_auto_reconnect_flow(self) -> None:
        os.environ["NAPCAT_SIMULATED_STATUS"] = "offline"
        from services.db.health_check import ensure_napcat_connected

        result = ensure_napcat_connected(max_retries=2, retry_interval=0)
        self.assertTrue(result)


if __name__ == "__main__":  # pragma: no cover - 调试入口
    unittest.main()
