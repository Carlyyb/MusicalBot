"""用户相关模型。"""
from __future__ import annotations

from typing import Optional

from sqlmodel import Field, SQLModel

from .base import SoftDelete, TimeStamped


class User(TimeStamped, SoftDelete, SQLModel, table=True):
    """QQ 用户实体，使用 QQ 号作为主键。"""

    __tablename__ = "users"

    user_id: str = Field(primary_key=True, description="QQ 号主键")
    nickname: Optional[str] = Field(default=None, description="用户昵称")
    active: bool = Field(default=True, description="是否仍然启用")
    transactions_success: int = Field(
        default=0, index=True, description="成功成交次数"
    )
    trust_score: float = Field(
        default=0.0, index=True, description="信任度评分"
    )
