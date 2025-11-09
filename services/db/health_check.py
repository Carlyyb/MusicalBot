"""NapCat 健康检查与自动重连工具。"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Callable, Optional

LOG_DIR = Path("logs")
ROOT_LOG_PATH = LOG_DIR / "musicalbot.log"
HEALTH_LOG_PATH = LOG_DIR / "health_check.log"
NETWORK_LOG_PATH = LOG_DIR / "network.log"
LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | "
    "request_id=%(request_id)s | user/group=%(actor)s | cmd=%(cmd)s | "
    "duration=%(duration)s | endpoint=%(endpoint)s | ok=%(ok)s | "
    "latency=%(latency_ms)sms | retry=%(retry_count)s"
)


class _ContextFilter(logging.Filter):
    """为日志记录补充默认上下文字段。"""

    _defaults = {
        "request_id": "-",
        "actor": "system",
        "cmd": "health_check",
        "duration": "0ms",
        "endpoint": "napcat://local",
        "ok": False,
        "latency_ms": 0,
        "retry_count": 0,
    }

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        for key, value in self._defaults.items():
            if not hasattr(record, key):
                setattr(record, key, value)
        return True


def _ensure_logger(logger: logging.Logger, path: Path) -> None:
    """确保日志记录器具备文件与过滤配置。"""

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    context_filter = _ContextFilter()

    if not any(isinstance(f, _ContextFilter) for f in logger.filters):
        logger.addFilter(context_filter)

    formatter = logging.Formatter(LOG_FORMAT)

    if not any(
        isinstance(handler, logging.FileHandler)
        and Path(getattr(handler, "baseFilename", "")) == path
        for handler in logger.handlers
    ):
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(context_filter)
        logger.addHandler(file_handler)

    if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.addFilter(context_filter)
        logger.addHandler(stream_handler)

    logger.setLevel(logging.INFO)


root_logger = logging.getLogger()
_ensure_logger(root_logger, ROOT_LOG_PATH)

health_logger = logging.getLogger("musicalbot.health")
_ensure_logger(health_logger, HEALTH_LOG_PATH)

network_logger = logging.getLogger("musicalbot.network")
_ensure_logger(network_logger, NETWORK_LOG_PATH)


def _default_ping() -> bool:
    """根据环境变量模拟 NapCat 心跳。"""

    status = os.getenv("NAPCAT_SIMULATED_STATUS", "online").lower()
    return status not in {"offline", "error", "down"}


def _default_reconnect() -> None:
    """模拟 NapCat 重连过程，并在成功时更新状态。"""

    os.environ["NAPCAT_SIMULATED_STATUS"] = "online"
    network_logger.info(
        "NapCat 重连流程已执行",
        extra={"actor": "napcat", "cmd": "auto_reconnect"},
    )


def _endpoint() -> str:
    return os.getenv("NAPCAT_ENDPOINT", "napcat://local")


def check_napcat_health(ping: Optional[Callable[[], bool]] = None) -> bool:
    """调用传入的 ping 方法检查 NapCat 是否健康。"""

    ping_func = ping or _default_ping
    start_ns = time.monotonic_ns()
    endpoint = _endpoint()

    try:
        healthy = bool(ping_func())
    except Exception:  # noqa: BLE001 捕获异常仅用于记录日志
        latency_ms = int((time.monotonic_ns() - start_ns) / 1_000_000)
        health_logger.exception(
            "NapCat 健康检查抛出异常",
            extra={
                "actor": "napcat",
                "cmd": "ping",
                "endpoint": endpoint,
                "ok": False,
                "latency_ms": latency_ms,
                "retry_count": 0,
            },
        )
        return False

    latency_ms = int((time.monotonic_ns() - start_ns) / 1_000_000)
    log_method = health_logger.info if healthy else health_logger.warning
    log_method(
        "NapCat 心跳检测完成",
        extra={
            "actor": "napcat",
            "cmd": "ping",
            "endpoint": endpoint,
            "ok": healthy,
            "latency_ms": latency_ms,
            "retry_count": 0,
        },
    )
    return healthy


def ensure_napcat_connected(
    ping: Optional[Callable[[], bool]] = None,
    reconnect: Optional[Callable[[], None]] = None,
    *,
    max_retries: int = 3,
    retry_interval: float = 5.0,
) -> bool:
    """若检测失败则尝试自动重连 NapCat。"""

    ping_func = ping or _default_ping
    reconnect_func = reconnect or _default_reconnect
    endpoint = _endpoint()

    if check_napcat_health(ping_func):
        return True

    health_logger.warning(
        "NapCat 健康检查失败，准备重试",
        extra={
            "actor": "napcat",
            "cmd": "auto_reconnect",
            "endpoint": endpoint,
            "ok": False,
            "latency_ms": 0,
            "retry_count": 0,
        },
    )

    start = time.monotonic()
    for attempt in range(1, max_retries + 1):
        try:
            reconnect_func()
        except Exception:  # noqa: BLE001 记录异常但继续重试
            health_logger.exception(
                "NapCat 重连过程出现异常",
                extra={
                    "actor": "napcat",
                    "cmd": "auto_reconnect",
                    "endpoint": endpoint,
                    "ok": False,
                    "retry_count": attempt,
                },
            )

        time.sleep(retry_interval)

        if check_napcat_health(ping_func):
            duration = time.monotonic() - start
            health_logger.info(
                "NapCat 重连成功",
                extra={
                    "actor": "napcat",
                    "cmd": "auto_reconnect",
                    "endpoint": endpoint,
                    "ok": True,
                    "latency_ms": int(duration * 1000),
                    "retry_count": attempt,
                },
            )
            return True

    duration = time.monotonic() - start
    health_logger.error(
        "NapCat 重连失败，请人工介入",
        extra={
            "actor": "napcat",
            "cmd": "auto_reconnect",
            "endpoint": endpoint,
            "ok": False,
            "latency_ms": int(duration * 1000),
            "retry_count": max_retries,
        },
    )
    return False


__all__ = [
    "check_napcat_health",
    "ensure_napcat_connected",
    "health_logger",
    "network_logger",
]
