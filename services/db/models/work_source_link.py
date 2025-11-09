"""剧目来源链接模型。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from .base import SoftDelete, TimeStamped


class WorkSourceLink(TimeStamped, SoftDelete, SQLModel, table=True):
    """不同数据源的剧目信息映射。"""

    __tablename__ = "work_source_links"
    __table_args__ = (
        UniqueConstraint(
            "work_id",
            "source",
            "source_id",
            name="uq_work_source_link",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    work_id: int = Field(foreign_key="plays.id", index=True, description="剧目主键")
    source: str = Field(index=True, description="外部数据源标识")
    source_id: str = Field(index=True, description="外部源中的主键")
    title_at_source: Optional[str] = Field(
        default=None, description="外部源展示标题"
    )
    city_hint: Optional[str] = Field(default=None, description="城市提示信息")
    confidence: float = Field(
        default=0.0, description="匹配置信度（0-1）"
    )
    last_sync_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="最后一次同步时间（UTC）",
    )
    payload_hash: Optional[str] = Field(
        default=None,
        index=True,
        description="源数据内容哈希，便于检测变更",
    )
