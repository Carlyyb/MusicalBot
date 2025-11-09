#!/usr/bin/env python3
#!/usr/bin/env python3
"""模拟 HLQ 轮询吞吐，评估 100-300 条事件的处理效率。"""
from __future__ import annotations

import argparse
import asyncio
import random
import time
from collections import deque
from typing import Deque, Dict, List

from services.hulaquan.hlq_polling import HLQPollingService


async def main(iterations: int, batch: int) -> None:
    queue: Deque[Dict[str, object]] = deque()
    for play_id in range(batch):
        queue.append(
            {
                "play_id": play_id,
                "city_norm": random.choice(["北京", "上海", "深圳"]),
                "snapshot": {"tickets": [play_id]},
                "payload_hash": f"seed-{play_id}",
            }
        )

    async def fetch() -> List[Dict[str, object]]:
        updates = []
        for _ in range(min(len(queue), batch)):
            item = queue.popleft()
            item["payload_hash"] = f"{item['payload_hash']}-{random.random():.3f}"
            updates.append(item)
            queue.append(item)
        return updates

    processed = 0

    async def on_update(event) -> None:
        nonlocal processed
        processed += 1

    service = HLQPollingService(fetch, on_update=on_update)

    start = time.perf_counter()
    for _ in range(iterations):
        await service.run_once()
    duration = time.perf_counter() - start
    print(f"运行 {iterations} 轮，总处理 {processed} 次更新，耗时 {duration:.3f}s")
    print(f"平均每轮耗时 {duration / max(iterations, 1):.4f}s")


def cli() -> None:
    parser = argparse.ArgumentParser(description="HLQ 轮询基准测试")
    parser.add_argument("--iterations", type=int, default=10, help="轮询次数")
    parser.add_argument("--batch", type=int, default=100, help="单次拉取事件数量")
    args = parser.parse_args()
    asyncio.run(main(args.iterations, args.batch))


if __name__ == "__main__":
    cli()
