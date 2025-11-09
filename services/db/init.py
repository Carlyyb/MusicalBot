"""数据库初始化脚本。"""
from __future__ import annotations

from typing import List, Sequence

from sqlalchemy import inspect
from sqlmodel import SQLModel

from .connection import DATABASE_PATH, get_engine
from .models import Group, Play, PlaySnapshot, Subscription, User, WorkAlias, WorkSourceLink


def init_db(*, engine=None, verbose: bool = True) -> Sequence[str]:
    """初始化 SQLite 数据库并创建所有表。"""

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    active_engine = engine or get_engine()
    SQLModel.metadata.create_all(active_engine)

    inspector = inspect(active_engine)
    tables: List[str] = sorted(inspector.get_table_names())

    if verbose:
        table_str = ", ".join(tables)
        print(f"数据库初始化完成，已创建数据表: {table_str}")

    return tables
