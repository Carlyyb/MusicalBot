"""剧目别名模型。"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from .base import SoftDelete, TimeStamped, WeightLevel


class WorkAlias(TimeStamped, SoftDelete, SQLModel, table=True):
    """剧目别名信息。"""

    __tablename__ = "work_aliases"

    id: Optional[int] = Field(default=None, primary_key=True)
    work_id: int = Field(foreign_key="plays.id", index=True, description="剧目主键")
    alias: str = Field(description="别名原文")
    alias_norm: str = Field(index=True, description="别名标准化形式")
    source: Optional[str] = Field(default=None, description="别名来源")
    weight: int = Field(
        default=WeightLevel.MEDIUM.value,
        description="别名权重，用于匹配排序",
    )
    no_response_count: int = Field(
        default=0,
        description="无响应计数，用于调节推荐权重",
    )
    last_used_at: Optional[datetime] = Field(
        default=None,
        description="最后一次被查询的时间（UTC）",
    )
