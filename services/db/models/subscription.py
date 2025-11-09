"""订阅相关模型。"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, SQLModel

from .base import (
    RoleType,
    SoftDelete,
    SubscriptionFrequency,
    SubscriptionTargetKind,
    TimeStamped,
)


class Subscription(TimeStamped, SoftDelete, SQLModel, table=True):
    """用户订阅关键词。"""

    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("user_id", "keyword", name="uq_subscription_user_keyword"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.user_id", index=True, description="用户主键")
    keyword: str = Field(index=True, description="订阅关键词")


class SubscriptionTarget(TimeStamped, SoftDelete, SQLModel, table=True):
    """订阅目标，描述剧目/演员/事件等细分对象。"""

    __tablename__ = "subscription_targets"
    __table_args__ = (
        UniqueConstraint(
            "subscription_id",
            "kind",
            "target_id",
            "name",
            name="uq_subscription_target",
        ),
        Index("ix_subscription_target_kind", "kind"),
        Index("ix_subscription_target_city", "city_filter"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    subscription_id: int = Field(
        foreign_key="subscriptions.id",
        index=True,
        description="关联订阅主键",
    )
    kind: SubscriptionTargetKind = Field(
        description="目标类别（剧目/演员/事件/关键词）",
    )
    target_id: Optional[str] = Field(
        default=None,
        index=True,
        description="若存在则指向外部 ID",
    )
    name: Optional[str] = Field(
        default=None,
        index=True,
        description="目标名称或关键词",
    )
    city_filter: Optional[str] = Field(
        default=None,
        description="城市过滤条件（标准化）",
    )
    flags: str = Field(
        default="{}",
        description="用于存放额外 JSON 配置的字符串",
    )


class SubscriptionOption(TimeStamped, SoftDelete, SQLModel, table=True):
    """订阅的通知选项。"""

    __tablename__ = "subscription_options"
    __table_args__ = (
        UniqueConstraint("subscription_id", name="uq_subscription_option"),
        Index("ix_subscription_option_freq", "freq"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    subscription_id: int = Field(
        foreign_key="subscriptions.id",
        unique=True,
        description="关联订阅主键",
    )
    mute: bool = Field(default=False, description="是否静默")
    freq: SubscriptionFrequency = Field(
        default=SubscriptionFrequency.REALTIME,
        description="通知频率",
    )
    allow_broadcast: bool = Field(default=True, description="是否允许群播")
    last_notified_at: Optional[datetime] = Field(
        default=None,
        description="最后一次推送时间（UTC）",
    )


class UserRole(TimeStamped, SoftDelete, SQLModel, table=True):
    """用户在全局或群组范围内的角色。"""

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "scope_group_id", "role", name="uq_user_role"),
        Index("ix_user_role_scope", "scope_group_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.user_id", index=True, description="用户主键")
    scope_group_id: Optional[str] = Field(
        default=None,
        description="所属群组，None 表示全局",
    )
    role: RoleType = Field(description="角色类型")


class Membership(TimeStamped, SoftDelete, SQLModel, table=True):
    """群组成员关系。"""

    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_membership"),
        Index("ix_membership_group", "group_id"),
        Index("ix_membership_user", "user_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: str = Field(foreign_key="groups.group_id", description="群组主键")
    user_id: str = Field(foreign_key="users.user_id", description="用户主键")
    role: RoleType = Field(default=RoleType.MEMBER, description="成员在群内的角色")
    joined_at: Optional[datetime] = Field(
        default=None,
        description="加入时间（UTC）",
    )
