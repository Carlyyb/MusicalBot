#!/usr/bin/env python3
"""模拟群发性能，用于评估 200-500 个目标的并发耗时。"""
from __future__ import annotations

import argparse
import asyncio
import random
import statistics
import time


async def _send_message(target: int, semaphore: asyncio.Semaphore) -> float:
    async with semaphore:
        start = time.perf_counter()
        await asyncio.sleep(random.uniform(0.01, 0.05))
        return time.perf_counter() - start


async def run_benchmark(targets: int, concurrency: int) -> None:
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [_send_message(idx, semaphore) for idx in range(targets)]
    durations = await asyncio.gather(*tasks)
    sorted_durations = sorted(durations)
    index = max(int(len(sorted_durations) * 0.95) - 1, 0)
    print(f"发送 {targets} 个目标完成，最大耗时 {max(durations):.3f}s")
    print(
        f"平均耗时 {statistics.mean(durations):.3f}s，p95={sorted_durations[index]:.3f}s"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="MusicalBot 群发基准测试")
    parser.add_argument("--targets", type=int, default=300, help="模拟的目标数量，默认 300")
    parser.add_argument("--concurrency", type=int, default=50, help="并发协程数，默认 50")
    args = parser.parse_args()

    asyncio.run(run_benchmark(args.targets, args.concurrency))


if __name__ == "__main__":
    main()
