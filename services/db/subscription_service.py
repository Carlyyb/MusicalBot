"""订阅相关的数据服务层。"""
from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Dict, Iterator, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from ..search.normalize import normalize_city, normalize_text
from .connection import get_session
from .models import (
    Subscription,
    SubscriptionFrequency,
    SubscriptionOption,
    SubscriptionTarget,
    SubscriptionTargetKind,
)


@contextmanager
def _session_scope(session: Optional[Session] = None) -> Iterator[Session]:
    """统一处理可选会话的上下文。"""

    if session is not None:
        yield session
    else:
        with get_session() as managed_session:
            yield managed_session


def _ensure_subscription(
    session: Session,
    user_id: str,
    keyword: str,
) -> Subscription:
    """查询或创建订阅主记录。"""

    statement = select(Subscription).where(
        Subscription.user_id == user_id,
        Subscription.keyword == keyword,
        Subscription.is_deleted.is_(False),
    )
    subscription = session.exec(statement).one_or_none()
    if subscription is None:
        subscription = Subscription(user_id=user_id, keyword=keyword)
        session.add(subscription)
        session.commit()
        session.refresh(subscription)
    return subscription


def _normalize_target_payload(target: Dict[str, object]) -> Dict[str, object]:
    payload = dict(target)
    if "name" in payload and isinstance(payload["name"], str):
        payload["name"] = normalize_text(payload["name"])
    if "city_filter" in payload and isinstance(payload["city_filter"], str):
        payload["city_filter"] = normalize_city(payload["city_filter"])
    return payload


def add_subscription(
    user_id: str,
    kind: SubscriptionTargetKind | str,
    target: Dict[str, object] | str,
    options: Optional[Dict[str, object]] = None,
    *,
    session: Optional[Session] = None,
) -> int:
    """为用户创建订阅并返回订阅主键。"""

    kind_enum = (
        kind if isinstance(kind, SubscriptionTargetKind) else SubscriptionTargetKind(kind)
    )

    if isinstance(target, str):
        target_payload: Dict[str, object] = {"name": target}
    else:
        target_payload = dict(target)

    normalized_payload = _normalize_target_payload(target_payload)
    name_value = normalized_payload.get("name") or target_payload.get("name")
    if not name_value and target_payload.get("target_id") is not None:
        name_value = str(target_payload.get("target_id"))
    keyword = str(name_value or target_payload.get("target_id") or kind_enum.value)

    flags_value = target_payload.get("flags", {})
    if not isinstance(flags_value, dict):
        raise ValueError("flags 字段必须是字典")

    city_filter = normalized_payload.get("city_filter")

    with _session_scope(session) as current_session:
        subscription = _ensure_subscription(current_session, user_id, keyword)

        target_record = SubscriptionTarget(
            subscription_id=subscription.id,
            kind=kind_enum,
            target_id=str(target_payload.get("target_id")) if target_payload.get("target_id") else None,
            name=str(name_value) if name_value else None,
            city_filter=str(city_filter) if city_filter else None,
            flags=json.dumps(flags_value, ensure_ascii=False),
        )

        current_session.add(target_record)
        try:
            current_session.commit()
        except IntegrityError as exc:  # noqa: TRY302
            current_session.rollback()
            raise ValueError("重复的订阅目标") from exc
        else:
            current_session.refresh(target_record)

        option_payload = options or {}
        freq_value = option_payload.get("freq", SubscriptionFrequency.REALTIME.value)
        freq_enum = (
            freq_value
            if isinstance(freq_value, SubscriptionFrequency)
            else SubscriptionFrequency(str(freq_value))
        )
        option_record = current_session.exec(
            select(SubscriptionOption).where(
                SubscriptionOption.subscription_id == subscription.id,
                SubscriptionOption.is_deleted.is_(False),
            )
        ).one_or_none()

        if option_record is None:
            option_record = SubscriptionOption(subscription_id=subscription.id)

        option_record.mute = bool(option_payload.get("mute", False))
        option_record.freq = freq_enum
        option_record.allow_broadcast = bool(option_payload.get("allow_broadcast", True))
        last_notified = option_payload.get("last_notified_at")
        if isinstance(last_notified, str):
            option_record.last_notified_at = datetime.fromisoformat(last_notified)
        elif isinstance(last_notified, datetime):
            option_record.last_notified_at = last_notified
        else:
            option_record.last_notified_at = None

        current_session.add(option_record)
        current_session.commit()
        current_session.refresh(subscription)
        return subscription.id


def list_subscriptions(
    user_id: str,
    *,
    kind: Optional[SubscriptionTargetKind | str] = None,
    session: Optional[Session] = None,
) -> List[Dict[str, object]]:
    """列出用户的订阅及其目标与选项。"""

    kind_enum = None
    if kind is not None:
        kind_enum = kind if isinstance(kind, SubscriptionTargetKind) else SubscriptionTargetKind(kind)

    with _session_scope(session) as current_session:
        sub_stmt = select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.is_deleted.is_(False),
        )
        subscriptions = list(current_session.exec(sub_stmt).all())
        if not subscriptions:
            return []

        sub_ids = [s.id for s in subscriptions]

        target_stmt = select(SubscriptionTarget).where(
            SubscriptionTarget.subscription_id.in_(sub_ids),
            SubscriptionTarget.is_deleted.is_(False),
        )
        if kind_enum is not None:
            target_stmt = target_stmt.where(SubscriptionTarget.kind == kind_enum)
        targets = list(current_session.exec(target_stmt).all())

        option_stmt = select(SubscriptionOption).where(
            SubscriptionOption.subscription_id.in_(sub_ids),
            SubscriptionOption.is_deleted.is_(False),
        )
        options = {record.subscription_id: record for record in current_session.exec(option_stmt).all()}

        bundles: List[Dict[str, object]] = []
        target_map: Dict[int, List[SubscriptionTarget]] = {}
        for record in targets:
            target_map.setdefault(record.subscription_id, []).append(record)

        for subscription in subscriptions:
            related_targets = target_map.get(subscription.id, [])
            if kind_enum is not None and not related_targets:
                continue
            bundles.append(
                {
                    "subscription": subscription,
                    "targets": related_targets,
                    "options": options.get(subscription.id),
                }
            )

        return bundles


def remove_subscription(
    user_id: str,
    kind: SubscriptionTargetKind | str,
    target: Dict[str, object] | str,
    *,
    session: Optional[Session] = None,
) -> bool:
    """软删除指定的订阅目标。"""

    kind_enum = kind if isinstance(kind, SubscriptionTargetKind) else SubscriptionTargetKind(kind)
    if isinstance(target, str):
        target_payload: Dict[str, object] = {"name": target}
    else:
        target_payload = dict(target)

    target_id = target_payload.get("target_id")
    target_name = target_payload.get("name")

    with _session_scope(session) as current_session:
        stmt = (
            select(SubscriptionTarget, Subscription)
            .join(Subscription, Subscription.id == SubscriptionTarget.subscription_id)
            .where(
                Subscription.user_id == user_id,
                Subscription.is_deleted.is_(False),
                SubscriptionTarget.kind == kind_enum,
                SubscriptionTarget.is_deleted.is_(False),
            )
        )
        if target_id is not None:
            stmt = stmt.where(SubscriptionTarget.target_id == str(target_id))
        if target_name is not None:
            stmt = stmt.where(SubscriptionTarget.name == str(target_name))

        pair = current_session.exec(stmt).one_or_none()
        if pair is None:
            return False

        target_record, subscription = pair
        target_record.is_deleted = True
        target_record.updated_at = datetime.now(timezone.utc)
        current_session.add(target_record)

        remaining_stmt = select(SubscriptionTarget).where(
            SubscriptionTarget.subscription_id == subscription.id,
            SubscriptionTarget.is_deleted.is_(False),
        )
        has_remaining = current_session.exec(remaining_stmt).first() is not None
        if not has_remaining:
            subscription.is_deleted = True
            subscription.updated_at = datetime.now(timezone.utc)
            current_session.add(subscription)

        current_session.commit()
        return True


__all__ = [
    "add_subscription",
    "list_subscriptions",
    "remove_subscription",
]
