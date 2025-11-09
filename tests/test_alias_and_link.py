"""别名与来源链接服务的单元测试。"""
from __future__ import annotations

import unittest

from sqlmodel import Session, SQLModel, create_engine

from services.db.alias_service import (
    add_alias,
    find_play_by_alias_or_name,
    link_source,
    record_no_response,
)
from services.db.models import Play, WorkAlias


class AliasServiceCase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            echo=False,
        )
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        play = Play(name="不眠之夜", name_norm="不眠之夜")
        self.session.add(play)
        self.session.commit()
        self.session.refresh(play)
        self.play_id = play.id

    def tearDown(self) -> None:
        self.session.close()

    def test_alias_add_and_lookup(self) -> None:
        add_alias(self.play_id, "《不眠之夜》", session=self.session)
        result = find_play_by_alias_or_name("不眠之夜", session=self.session)
        self.assertEqual(result, self.play_id)

        count = record_no_response("不眠之夜", session=self.session)
        self.assertEqual(count, 1)
        alias = self.session.get(WorkAlias, 1)
        assert alias is not None
        self.assertEqual(alias.no_response_count, 1)

    def test_source_link_upsert(self) -> None:
        link = link_source(
            self.play_id,
            "hlq",
            "123",
            title_at_source="不眠之夜",
            payload_hash="hash1",
            session=self.session,
        )
        self.assertEqual(link.source_id, "123")

        updated = link_source(
            self.play_id,
            "hlq",
            "123",
            city_hint="上海",
            payload_hash="hash2",
            session=self.session,
        )
        self.assertEqual(updated.id, link.id)
        self.assertEqual(updated.payload_hash, "hash2")
        self.assertEqual(updated.city_hint, "上海")


if __name__ == "__main__":  # pragma: no cover - 调试入口
    unittest.main()
