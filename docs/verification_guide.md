# MusicalBot V0.5 功能验证指引

> 所有示例均默认在项目根目录执行，并假设已经安装 `requirements.txt` 中列出的依赖。

## 1. 数据库连接验证

```bash
python -c "from services.db.init import init_db; init_db()"
```

执行完成后应打印创建的表名，可使用 SQLite Browser 等工具打开 `data/musicalbot.db`，核对是否存在 `users`、`subscriptions`、`groups`、`plays`、`play_snapshots` 等表。

## 2. 基础 CRUD 验证

```bash
python -m unittest
```

单元测试覆盖用户、订阅、群组服务的核心接口，确保 `add_user()`、`get_user_by_id()`、`update_user_activity()`、`add_subscription()`、`get_user_subscriptions()`、`create_group()`、`get_groups_for_user()` 均能返回预期结果。

## 3. Play 快照与事件验证

```bash
python -c "from services.play.snapshot_manager import rebuild_snapshot; rebuild_snapshot(1)"
```

如剧目 ID 不存在会抛出异常，请先创建剧目或在单元测试环境中执行。命令成功后，将在 `play_snapshots` 表中生成最新快照，`payload` 字段包含自动生成的元数据。

## 4. 健康检查与自动重连

```bash
python -c "from services.db.health_check import check_napcat_health, ensure_napcat_connected; check_napcat_health(); ensure_napcat_connected()"
```

使用环境变量 `NAPCAT_SIMULATED_STATUS=offline` 可模拟断连，脚本会尝试自动重连并在日志中记录“NapCat 重连成功”或“NapCat 重连失败”。

## 5. 日志与告警检查

```bash
python scripts/verify_logs.py
```

脚本会检查 `logs/musicalbot.log` 是否存在以及是否包含 `timestamp`、`level`、`module`、`request_id`、`user/group`、`cmd`、`duration` 等关键字段。可结合健康检查脚本生成的日志进一步核对。
