"""数据库连接与会话管理。"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

DATABASE_PATH = Path("data/musicalbot.db")
DATABASE_URL = "sqlite:///data/musicalbot.db?check_same_thread=False"


def _apply_sqlite_pragmas(engine: Engine) -> None:
    """为 SQLite 引擎配置 WAL 与同步模式。"""

    if "sqlite" not in engine.url.drivername:
        return
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA journal_mode=WAL")
        connection.exec_driver_sql("PRAGMA synchronous=NORMAL")


def _build_engine(url: str, *, echo: bool = False) -> Engine:
    """内部统一的引擎构造函数。"""

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        url,
        echo=echo,
        connect_args={"check_same_thread": False},
        future=True,
    )
    _apply_sqlite_pragmas(engine)
    return engine


# SQLite 在多线程场景需要禁用同线程检查
_engine: Engine = _build_engine(DATABASE_URL)


def set_engine(engine: Engine) -> Engine:
    """覆盖默认引擎，便于测试或临时切换数据库。"""

    global _engine
    _engine = engine
    _apply_sqlite_pragmas(_engine)
    return _engine


def configure_engine(url: Optional[str] = None, *, echo: bool = False) -> Engine:
    """根据传入的 URL 重新构建引擎。"""

    global _engine, DATABASE_URL
    if url is not None:
        DATABASE_URL = url
    _engine = _build_engine(DATABASE_URL, echo=echo)
    return _engine


def get_engine() -> Engine:
    """获取当前使用的数据库引擎。"""

    return _engine


@contextmanager
def get_session(engine: Optional[Engine] = None) -> Iterator[Session]:
    """提供一个自动提交/回滚的会话上下文。"""

    # 确保数据库文件夹存在
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    working_engine = engine or _engine
    with Session(working_engine) as session:
        yield session
