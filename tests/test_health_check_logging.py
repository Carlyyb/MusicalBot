"""健康检查日志输出的单元测试。"""
from __future__ import annotations

import importlib
import os
import tempfile
import unittest
from pathlib import Path


class HealthCheckLoggingCase(unittest.TestCase):
    def test_health_log_contains_fields(self) -> None:
        original_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                os.chdir(tmp)
                module = importlib.import_module("services.db.health_check")
                importlib.reload(module)

                module.check_napcat_health(lambda: True)
                log_file = Path("logs/health_check.log")
                self.assertTrue(log_file.exists())
                content = log_file.read_text(encoding="utf-8").strip().splitlines()
                self.assertTrue(
                    any("endpoint=" in line and "retry=" in line for line in content)
                )
        finally:
            os.chdir(original_cwd)
            importlib.reload(importlib.import_module("services.db.health_check"))


if __name__ == "__main__":  # pragma: no cover - 调试入口
    unittest.main()
