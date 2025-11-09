"""兼容旧 JSON UsersManager 的服务入口，内部已转调 DB/Service。"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Dict, Iterator, List, Optional

from sqlmodel import Session, select

from ..db.connection import get_session
from ..db.models import Membership, RoleType, SubscriptionTargetKind, UserRole
from ..db.subscription_service import add_subscription, list_subscriptions


@contextmanager
def _session_scope(session: Optional[Session] = None) -> Iterator[Session]:
    if session is not None:
        yield session
    else:
        with get_session() as managed_session:
            yield managed_session


def subscribe_tickets(
    user_id: str,
    play_or_keyword: Dict[str, object] | str,
    options: Optional[Dict[str, object]] = None,
    *,
    session: Optional[Session] = None,
) -> int:
    """兼容旧接口的订阅票务方法。"""

    return add_subscription(
        user_id,
        SubscriptionTargetKind.PLAY,
        play_or_keyword,
        options,
        session=session,
    )


def add_event_subscribe(
    user_id: str,
    event_payload: Dict[str, object] | str,
    options: Optional[Dict[str, object]] = None,
    *,
    session: Optional[Session] = None,
) -> int:
    """兼容事件订阅的写入入口。"""

    return add_subscription(
        user_id,
        SubscriptionTargetKind.EVENT,
        event_payload,
        options,
        session=session,
    )


def list_subs(
    user_id: str,
    kind: Optional[SubscriptionTargetKind | str] = None,
    *,
    session: Optional[Session] = None,
) -> List[Dict[str, object]]:
    """列出用户订阅，返回结构与旧管理器近似。"""

    bundles = list_subscriptions(user_id, kind=kind, session=session)
    results: List[Dict[str, object]] = []
    for bundle in bundles:
        subscription = bundle["subscription"]
        targets = bundle["targets"]
        option = bundle.get("options")
        results.append(
            {
                "id": subscription.id,
                "keyword": subscription.keyword,
                "targets": [
                    {
                        "kind": target.kind.value,
                        "target_id": target.target_id,
                        "name": target.name,
                        "city_filter": target.city_filter,
                        "flags": target.flags,
                    }
                    for target in targets
                ],
                "options": {
                    "mute": bool(option.mute) if option else False,
                    "freq": option.freq.value if option else "realtime",
                    "allow_broadcast": bool(option.allow_broadcast) if option else True,
                    "last_notified_at": option.last_notified_at.isoformat()
                    if option and option.last_notified_at
                    else None,
                },
            }
        )
    return results


def has_permission(
    user_id: str,
    group_id: Optional[str],
    *,
    role: str = "op",
    session: Optional[Session] = None,
) -> bool:
    """校验用户是否拥有指定权限。"""

    desired = RoleType(role)
    now = datetime.now(timezone.utc)

    with _session_scope(session) as current_session:
        def _match_role(record_role: RoleType) -> bool:
            if desired == RoleType.ADMIN:
                return record_role == RoleType.ADMIN
            if desired == RoleType.OP:
                return record_role in {RoleType.OP, RoleType.ADMIN}
            return True

        role_stmt = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.is_deleted.is_(False),
        )
        roles = current_session.exec(role_stmt).all()
        for record in roles:
            if record.scope_group_id is None and _match_role(record.role):
                record.updated_at = now
                current_session.add(record)
                current_session.commit()
                return True

        if group_id is not None:
            for record in roles:
                if record.scope_group_id == str(group_id) and _match_role(record.role):
                    record.updated_at = now
                    current_session.add(record)
                    current_session.commit()
                    return True

            membership_stmt = select(Membership).where(
                Membership.user_id == user_id,
                Membership.group_id == str(group_id),
                Membership.is_deleted.is_(False),
            )
            membership = current_session.exec(membership_stmt).one_or_none()
            if membership and _match_role(membership.role):
                membership.updated_at = now
                current_session.add(membership)
                current_session.commit()
                return True

    return False


__all__ = [
    "subscribe_tickets",
    "add_event_subscribe",
    "list_subs",
    "has_permission",
]
