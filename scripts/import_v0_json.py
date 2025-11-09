#!/usr/bin/env python3
"""V0 JSON 数据迁移脚本骨架。"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable

from services.db.alias_service import add_alias, link_source
from services.db.subscription_service import add_subscription
from services.db.user_service import add_user
from services.db.models import SubscriptionTargetKind

DATA_DIR = Path("plugins/Hulaquan/data/data_manager")


def iter_json_files() -> Iterable[Path]:
    if not DATA_DIR.exists():
        return []
    return DATA_DIR.glob("*.json")


def import_users(payload: Dict[str, object]) -> None:
    for user_id, info in payload.get("users", {}).items():
        add_user(user_id, nickname=info.get("nickname"))


def import_subscriptions(payload: Dict[str, object]) -> None:
    for entry in payload.get("subscribe_tickets", []):
        add_subscription(
            entry["user_id"],
            SubscriptionTargetKind.PLAY,
            {"name": entry["title"], "flags": entry},
        )


def import_aliases(payload: Dict[str, object]) -> None:
    for alias in payload.get("aliases", []):
        add_alias(alias["play_id"], alias["alias"], source=alias.get("source", "json"))
        if alias.get("source_link"):
            link_source(
                alias["play_id"],
                alias["source_link"]["source"],
                alias["source_link"]["id"],
                title_at_source=alias["alias"],
            )


def main() -> None:
    success = failures = 0
    for path in iter_json_files():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # noqa: PERF203 - 仅用于快速骨架
            print(f"解析失败: {path.name}: {exc}")
            failures += 1
            continue

        import_users(payload)
        import_subscriptions(payload)
        import_aliases(payload)
        success += 1

    print(
        f"导入完成：成功 {success} 个文件，失败 {failures} 个文件，时间 {datetime.now(timezone.utc).isoformat()}"
    )


if __name__ == "__main__":
    main()
