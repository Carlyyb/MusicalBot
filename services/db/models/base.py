"""数据库模型基础定义与通用枚举。"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


class TimeStamped(SQLModel, table=False):
    """为所有表提供创建与更新时间字段。"""

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="记录创建时间（UTC）",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="最后一次更新时间（UTC）",
    )


class SoftDelete(SQLModel, table=False):
    """软删除标记，便于逻辑删除记录。"""

    is_deleted: bool = Field(default=False, description="是否已被逻辑删除")


class GroupType(str, Enum):
    """群组类型枚举。"""

    BROADCAST = "broadcast"
    FILTERED = "filtered"
    PASSIVE = "passive"


class WeightLevel(int, Enum):
    """别名权重常用等级。"""

    LOW = 1
    MEDIUM = 5
    HIGH = 10


class SubscriptionTargetKind(str, Enum):
    """订阅目标的类型枚举。"""

    PLAY = "PLAY"
    ACTOR = "ACTOR"
    EVENT = "EVENT"
    KEYWORD = "KEYWORD"


class SubscriptionFrequency(str, Enum):
    """通知频率配置。"""

    REALTIME = "realtime"
    HOURLY = "hourly"
    DAILY = "daily"


class RoleType(str, Enum):
    """角色类型定义。"""

    ADMIN = "admin"
    OP = "op"
    MEMBER = "member"
