"""剧目缓存快照模型。"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.sqlite import JSON
from sqlmodel import Field, SQLModel

from .base import SoftDelete, TimeStamped


class PlaySnapshot(TimeStamped, SoftDelete, SQLModel, table=True):
    """用于缓存聚合后的剧目信息。"""

    __tablename__ = "play_snapshots"

    id: Optional[int] = Field(default=None, primary_key=True)
    play_id: int = Field(foreign_key="plays.id", index=True, description="剧目主键")
    city_norm: Optional[str] = Field(default=None, description="城市标准化名称")
    payload: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="缓存的聚合结果",
    )
    last_success_at: Optional[datetime] = Field(
        default=None, description="最后一次成功更新时间（UTC）"
    )
    ttl_seconds: int = Field(default=0, description="缓存有效期（秒）")
