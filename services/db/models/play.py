"""剧目信息模型。"""
from __future__ import annotations

from typing import Optional

from sqlmodel import Field, SQLModel

from .base import SoftDelete, TimeStamped


class Play(TimeStamped, SoftDelete, SQLModel, table=True):
    """剧目信息主表。"""

    __tablename__ = "plays"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="剧目原始名称")
    name_norm: str = Field(index=True, description="标准化名称")
    default_city_norm: Optional[str] = Field(
        default=None, description="默认城市（标准化）"
    )
    note: Optional[str] = Field(default=None, description="补充备注")
