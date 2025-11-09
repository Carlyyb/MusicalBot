"""群组相关模型。"""
from __future__ import annotations

from typing import Optional

from sqlmodel import Field, SQLModel

from .base import GroupType, SoftDelete, TimeStamped


class Group(TimeStamped, SoftDelete, SQLModel, table=True):
    """机器人服务所需的 QQ 群信息。"""

    __tablename__ = "groups"

    group_id: str = Field(primary_key=True, description="QQ群号")
    name: Optional[str] = Field(default=None, description="群名称")
    group_type: GroupType = Field(
        default=GroupType.BROADCAST, description="群组类型"
    )
    active: bool = Field(default=True, description="是否仍参与服务")
