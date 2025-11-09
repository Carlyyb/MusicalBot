"""群组相关的数据服务层。"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, List, Optional

from sqlmodel import Session, select

from .connection import get_session
from .models import Group, GroupType


@contextmanager
def _session_scope(session: Optional[Session] = None) -> Iterator[Session]:
    """统一处理可选会话的上下文。"""

    if session is not None:
        yield session
    else:
        with get_session() as managed_session:
            yield managed_session


def create_group(
    group_id: str,
    *,
    name: Optional[str] = None,
    group_type: GroupType = GroupType.BROADCAST,
    active: bool = True,
    session: Optional[Session] = None,
) -> Group:
    """创建一个群组记录。"""

    with _session_scope(session) as current_session:
        group = Group(
            group_id=group_id,
            name=name,
            group_type=group_type,
            active=active,
        )
        current_session.add(group)
        current_session.commit()
        current_session.refresh(group)
        return group


def get_groups_for_user(
    user_id: str, *, session: Optional[Session] = None
) -> List[Group]:
    """获取与用户相关的群组列表，占位逻辑返回所有启用群。"""

    with _session_scope(session) as current_session:
        statement = select(Group).where(
            Group.active.is_(True),
            Group.is_deleted.is_(False),
        )
        return list(current_session.exec(statement).all())
