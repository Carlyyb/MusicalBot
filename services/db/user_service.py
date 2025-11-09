"""用户相关的数据服务层。"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Optional

from sqlmodel import Session

from .connection import get_session
from .models import User


@contextmanager
def _session_scope(session: Optional[Session] = None) -> Iterator[Session]:
    """统一处理可选会话的上下文。"""

    if session is not None:
        yield session
    else:
        with get_session() as managed_session:
            yield managed_session


def get_user_by_id(user_id: str, session: Optional[Session] = None) -> Optional[User]:
    """根据 QQ 号查询用户。"""

    with _session_scope(session) as current_session:
        return current_session.get(User, user_id)


def add_user(
    user_id: str,
    nickname: Optional[str] = None,
    *,
    session: Optional[Session] = None,
) -> User:
    """创建并返回一个用户。"""

    with _session_scope(session) as current_session:
        user = User(user_id=user_id, nickname=nickname)
        current_session.add(user)
        current_session.commit()
        current_session.refresh(user)
        return user


def update_user_activity(
    user_id: str, active: bool, *, session: Optional[Session] = None
) -> Optional[User]:
    """更新用户的活跃状态。"""

    with _session_scope(session) as current_session:
        user = current_session.get(User, user_id)
        if not user:
            return None

        user.active = active
        user.updated_at = datetime.now(timezone.utc)
        current_session.add(user)
        current_session.commit()
        current_session.refresh(user)
        return user
