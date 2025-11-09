"""简单的日志字段验证脚本。"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Tuple

LOG_FILE = Path("logs/musicalbot.log")
TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T?\s?\d{2}:")
REQUIRED_TOKENS = ("request_id=", "user/group=", "cmd=", "duration=")


def validate_log_line(line: str) -> Tuple[bool, str]:
    """检查单行日志是否包含所需的关键字段。"""

    if not line.strip():
        return False, "空行"
    if not TIMESTAMP_PATTERN.match(line):
        return False, "缺少 timestamp 字段"
    missing = [token for token in REQUIRED_TOKENS if token not in line]
    if missing:
        return False, f"缺少字段: {', '.join(missing)}"
    return True, ""


def verify_log_file(path: Path = LOG_FILE) -> bool:
    """逐行检查日志文件是否符合格式要求。"""

    if not path.exists():
        print(f"未找到日志文件: {path}")
        return False

    all_valid = True
    line_count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_count, line in enumerate(handle, start=1):
            valid, reason = validate_log_line(line)
            if not valid:
                all_valid = False
                print(f"第 {line_count} 行校验失败: {reason}")
    if all_valid:
        print(f"日志校验通过，共检查 {line_count} 行")
    return all_valid


if __name__ == "__main__":
    verify_log_file()
