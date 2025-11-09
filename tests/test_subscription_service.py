"""订阅服务扩展能力的单元测试。"""
from __future__ import annotations

import unittest

from sqlmodel import Session, SQLModel, create_engine

from services.db.models import SubscriptionTargetKind
from services.db.subscription_service import (
    add_subscription,
    list_subscriptions,
    remove_subscription,
)
from services.db.user_service import add_user


class SubscriptionServiceCase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            echo=False,
        )
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        add_user("u1", nickname="用户1", session=self.session)

    def tearDown(self) -> None:
        self.session.close()

    def test_add_subscription_with_options(self) -> None:
        subscription_id = add_subscription(
            "u1",
            SubscriptionTargetKind.PLAY,
            {"name": "哈姆雷特", "city_filter": "上海"},
            options={"mute": True, "freq": "daily", "allow_broadcast": False},
            session=self.session,
        )
        bundles = list_subscriptions("u1", session=self.session)
        self.assertEqual(len(bundles), 1)
        bundle = bundles[0]
        self.assertEqual(bundle["subscription"].id, subscription_id)
        self.assertEqual(bundle["options"].freq.value, "daily")
        target = bundle["targets"][0]
        self.assertEqual(target.kind, SubscriptionTargetKind.PLAY)
        self.assertEqual(target.city_filter, "上海")

    def test_unique_target_constraint(self) -> None:
        add_subscription(
            "u1",
            SubscriptionTargetKind.EVENT,
            {"target_id": "E1", "flags": {"mode": 1}},
            session=self.session,
        )
        with self.assertRaises(ValueError):
            add_subscription(
                "u1",
                SubscriptionTargetKind.EVENT,
                {"target_id": "E1"},
                session=self.session,
            )

    def test_remove_subscription_soft_delete(self) -> None:
        add_subscription(
            "u1",
            SubscriptionTargetKind.KEYWORD,
            {"name": "演唱会"},
            session=self.session,
        )
        bundles = list_subscriptions("u1", session=self.session)
        self.assertEqual(len(bundles), 1)
        removed = remove_subscription(
            "u1",
            SubscriptionTargetKind.KEYWORD,
            {"name": "演唱会"},
            session=self.session,
        )
        self.assertTrue(removed)
        bundles = list_subscriptions("u1", session=self.session)
        self.assertEqual(len(bundles), 0)


if __name__ == "__main__":  # pragma: no cover - 调试入口
    unittest.main()
