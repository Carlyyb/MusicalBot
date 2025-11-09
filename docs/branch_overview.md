# work 分支改动速览

本文梳理当前分支新增/改动的主要模块，帮助工程师在接手 MusicalBot V0.5 架构时迅速建立整体感知。

## 核心成果
- **数据库层系统化**：统一由 `services.db` 聚合连接、模型与服务，并对 SQLite 启用 WAL/`synchronous=NORMAL` 等优化以适配 2C2G 服务器。【F:services/db/__init__.py†L1-L76】【F:services/db/connection.py†L1-L76】
- **订阅/权限模型扩展**：引入订阅目标、通知选项、角色与群成员等表结构，为后续兼容旧 JSON 订阅逻辑提供数据基础。【F:services/db/models/subscription.py†L19-L139】
- **别名与来源服务完善**：别名写入、模糊匹配、无响应计数与来源链接 upsert 均封装在服务层，支持 NapCat 事件链路复用。【F:services/db/alias_service.py†L1-L207】【F:services/db/models/work_alias.py†L1-L26】【F:services/db/models/work_source_link.py†L1-L33】
- **事件驱动缓存**：HLQ 轮询触发 `rebuild_snapshot`，缓存读取具备 TTL 检测与后台刷新，确保 Play 数据在更新后及时失效。【F:services/hulaquan/hlq_polling.py†L1-L154】【F:services/play/snapshot_manager.py†L1-L156】
- **兼容适配层**：提供旧插件签名一致的 `UsersManager`/`AliasManager`/`HLQManager`，内部全部转调数据库服务，便于平滑切换。【F:services/compat/users_manager.py†L1-L156】【F:services/compat/alias_manager.py†L1-L44】【F:services/compat/hlq_manager.py†L1-L51】
- **日志与健康检查分流**：NapCat 心跳、重连与网络日志落到独立文件，记录 endpoint、latency、retry 等上下文字段，满足运维监控需求。【F:services/db/health_check.py†L1-L217】
- **搜索规范化工具**：统一处理别名/城市文本的大小写、全半角与符号，确保查询与索引一致性。【F:services/search/normalize.py†L1-L32】

## 目录映射一览
- `services/db/models/`：全部 SQLModel 定义，含 TimeStamped/SoftDelete 继承与索引约束，便于 ORM 统一管理。【F:services/db/models/subscription.py†L19-L139】
- `services/db/*.py`：数据库连接、建表、服务（用户/订阅/群组/别名/健康检查）集中在此，插件只需调用公开函数。【F:services/db/__init__.py†L1-L76】
- `services/compat/`：封装旧管理器接口，保证原插件 import 替换后仍可工作，且自动使用新服务层。【F:services/compat/users_manager.py†L1-L156】
- `services/hulaquan/` 与 `services/play/`：HLQ 轮询与剧目快照管理，负责事件驱动的缓存刷新。【F:services/hulaquan/hlq_polling.py†L1-L154】【F:services/play/snapshot_manager.py†L1-L156】
- `services/search/`：文本规范化工具，供订阅、别名等模块统一调用。【F:services/search/normalize.py†L1-L32】
- `scripts/`：压测、日志核查与 V0 JSON 导入骨架，为迁移与性能验证提供入口。【F:scripts/bench_broadcast.py†L1-L34】【F:scripts/bench_polling.py†L1-L44】【F:scripts/import_v0_json.py†L1-L71】
- `tests/`：新增多组单元测试覆盖订阅、别名、快照、健康检查等关键流程，便于回归确认。【F:tests/test_db_services.py†L1-L148】【F:tests/test_subscription_service.py†L1-L84】【F:tests/test_alias_and_link.py†L1-L70】【F:tests/test_snapshot_and_events.py†L1-L99】【F:tests/test_health_check_logging.py†L1-L33】

## 关键模块速览
### 订阅体系
- `add_subscription` 会自动标准化目标名称/城市、维护唯一约束，并在同事务内写入通知选项；`list_subscriptions` 返回带目标与选项的打包结果，兼顾旧接口结构；`remove_subscription` 采用软删除策略并在最后一个目标移除时标记订阅失效。【F:services/db/subscription_service.py†L1-L208】
- 兼容层的 `subscribe_tickets`/`add_event_subscribe`/`list_subs` 直接转调上述服务并返回旧 JSON 管理器习惯的字段，`has_permission` 基于 UserRole/Membership 判断全局或群级权限。【F:services/compat/users_manager.py†L24-L153】

### 别名与来源管理
- 服务层负责别名写入、候选合并与无响应计数自增，来源链接支持 upsert 并记录最近同步时间与 payload hash，为事件去重提供依据。【F:services/db/alias_service.py†L27-L207】
- 兼容层 `AliasManager` 保留 `add_alias`/`find_by_alias`/`record_no_response` 接口，让旧插件在不改调用逻辑的前提下使用数据库存储。【F:services/compat/alias_manager.py†L21-L43】

### HLQ 轮询与剧目快照
- `HLQPollingService` 支持自适应 15/30/90 秒间隔、失败重试、并发上限控制，并将变更事件传入回调（默认刷新缓存）。【F:services/hulaquan/hlq_polling.py†L30-L154】
- `get_play_full` 在读取缓存时执行 TTL 校验，若过期会在后台重建并返回 `stale` 标记；`rebuild_snapshot` 负责生成/更新快照记录并写入最后成功时间。【F:services/play/snapshot_manager.py†L29-L153】
- 兼容层 `HLQManager` 允许旧代码通过剧目 ID 或来源 ID 获取最新快照与原始 payload。【F:services/compat/hlq_manager.py†L18-L51】

### 健康检查与日志
- `check_napcat_health`/`ensure_napcat_connected` 记录 endpoint、latency、retry、ok 等字段，日志分别输出到 `musicalbot.log`、`health_check.log` 与 `network.log`，便于排查网络问题。【F:services/db/health_check.py†L10-L217】
- `tests/test_health_check_logging.py` 验证 health log 是否生成及关键字段是否存在，保证运维脚本可直接消费。【F:tests/test_health_check_logging.py†L11-L29】

### 文本规范化
- `normalize_text`/`normalize_city` 提供统一的 Unicode 规范化、符号剥离与小写化逻辑，缓存至 LRU，供别名、订阅等场景使用。【F:services/search/normalize.py†L8-L32】

## 测试与工具链
- 订阅/别名/快照/健康检查均有独立单元测试，覆盖唯一约束、TTL 过期、HLQ 去重、日志字段等核心分支，可直接运行 `python -m unittest` 验证。【F:tests/test_subscription_service.py†L31-L79】【F:tests/test_alias_and_link.py†L35-L67】【F:tests/test_snapshot_and_events.py†L33-L96】【F:tests/test_db_services.py†L34-L147】
- `bench_broadcast.py`/`bench_polling.py` 用于在 tmux 下快速估算群发与 HLQ 更新吞吐；`import_v0_json.py` 提供旧 JSON 数据导入骨架，迁移时可逐步完善字段映射。【F:scripts/bench_broadcast.py†L9-L33】【F:scripts/bench_polling.py†L12-L42】【F:scripts/import_v0_json.py†L24-L66】
- `docs/verification_guide.md` 列出基础验证命令，适用于接入测试或回归检查。【F:docs/verification_guide.md†L5-L43】

## 快速掌控步骤建议
1. 参考验证指引运行 `init_db` 与单元测试，确认本地环境无误。【F:docs/verification_guide.md†L5-L20】
2. 根据兼容层接口替换旧插件 import（`UsersManager`/`AliasManager`/`HLQManager`），观察日志输出验证是否命中数据库服务。【F:services/compat/users_manager.py†L24-L99】【F:services/db/health_check.py†L73-L200】
3. 若需扩展订阅字段或别名策略，直接在对应服务层调整业务逻辑并补充单元测试即可，旧插件无需改动即可获益。【F:services/db/subscription_service.py†L39-L208】【F:tests/test_subscription_service.py†L31-L79】
4. 对接 HLQ 实际数据源时，实现自定义 fetcher 并传入 `HLQPollingService`，同时观察 `network.log` 与快照 `stale` 标记判断事件流是否正常。【F:services/hulaquan/hlq_polling.py†L30-L154】【F:services/play/snapshot_manager.py†L140-L153】

