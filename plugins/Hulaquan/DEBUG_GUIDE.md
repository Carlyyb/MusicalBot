# 呼啦圈上新通知调试指南

## 问题：用户反馈上新不会提示

### 可能的原因

1. **定时任务未运行**
2. **用户关注模式设置错误**
3. **数据比对逻辑问题**（`Hlq.compare_to_database_async()`）
4. **消息生成逻辑问题**（`__generate_announce_text`）
5. **消息发送失败**（API调用问题）
6. **数据刷新间隔太长**，用户在刷新前已经手动查看

---

## 调试流程

### 第一步：检查定时任务状态

使用命令：
```
/debug通知 check
```

查看内容：
- ✅ 定时任务是否在运行中？
- ⏰ 检测间隔是多少秒？
- 🔄 任务是否已完成（应该是"否"）？

**如果任务未运行：**
```
/呼啦圈检测  # 管理员命令，开启检测
```

---

### 第二步：检查用户设置

使用命令：
```
/debug通知 user
```

查看内容：
- 📌 **全局模式**是什么？
  - 模式0：不接受任何通知 ❌
  - 模式1：上新/补票 ✅
  - 模式2：上新/补票/回流 ✅
  - 模式3：上新/补票/回流/增减票 ✅

- 📋 是否关注了特定剧目？
- 🎫 是否关注了特定场次？

**常见问题：**
- ❌ 用户模式设置为 0（不接受通知）
  - 解决：`/呼啦圈通知 1` （或 2、3）

- ❌ 用户只关注了特定剧目/场次，但上新的是其他剧目
  - 解决：设置全局模式，或关注更多剧目

---

### 第三步：使用模拟数据测试

使用命令：
```
/debug通知 mock
```

这会：
1. 创建 4 张模拟票（上新、补票、回流）
2. 根据你的设置生成通知消息
3. 显示消息预览

**如果没有生成消息：**
说明问题在用户设置层面，回到第二步检查。

**如果生成了消息：**
说明消息生成逻辑正常，问题可能在：
- 数据比对环节（没有检测到真实的上新）
- 消息发送环节

---

### 第四步：检查真实数据比对

手动触发一次刷新：
```
/refresh  # 管理员命令
```

观察：
- 是否收到通知？
- 日志中是否有错误？

**查看日志：**
```powershell
# 查看最新日志
Get-Content f:\MusicalBot\logs\bot.log -Tail 50
```

关键日志搜索：
```powershell
# 搜索"呼啦圈"相关日志
Select-String -Path f:\MusicalBot\logs\bot.log -Pattern "呼啦圈|hulaquan|announcer" | Select-Object -Last 20
```

---

### 第五步：深度调试（代码层面）

如果以上步骤都正常，但仍然没有通知，需要：

#### 5.1 添加详细日志

在 `on_hulaquan_announcer` 方法中添加日志：

```python
@user_command_wrapper("hulaquan_announcer")
async def on_hulaquan_announcer(self, test=False, manual=False, announce_admin_only=False):
    log.info(f"🔄 开始执行呼啦圈上新检测，manual={manual}, announce_admin_only={announce_admin_only}")
    
    try:
        result = await Hlq.compare_to_database_async()
        
        # 添加详细日志
        log.info(f"📊 数据比对结果统计：")
        for cat, items in result["categorized"].items():
            if items:
                log.info(f"  - {cat}: {len(items)} 条")
        
        # ... 原有代码
        
        # 在发送消息时添加日志
        for user_id, user in _users.items():
            messages = self.__generate_announce_text(...)
            log.info(f"👤 为用户 {user_id} 生成了 {len(messages)} 组消息")
            
            for i in messages:
                m = "\n\n".join(i)
                log.info(f"📤 准备发送消息给 {user_id}，长度: {len(m)}")
                r = await self.api.post_private_msg(user_id, m)
                log.info(f"📬 发送结果: retcode={r.get('retcode')}")
                # ...
```

#### 5.2 检查 `Hlq.compare_to_database_async()` 

这是关键的数据比对方法，需要确认：
- 是否正常连接到呼啦圈API？
- 是否正确比对了新旧数据？
- `categorized` 字典中是否有数据？

添加测试代码：

```python
# 在 Python REPL 或测试脚本中
from plugins.Hulaquan.data_managers import Hlq
import asyncio

async def test_compare():
    result = await Hlq.compare_to_database_async()
    print("Events:", len(result.get("events", {})))
    print("Categorized:")
    for cat, items in result.get("categorized", {}).items():
        print(f"  {cat}: {len(items)}")
    return result

# 运行
result = asyncio.run(test_compare())
```

#### 5.3 测试消息生成逻辑

使用 `debug_announcer.py` 中的工具：

```python
from plugins.Hulaquan.debug_announcer import AnnouncerDebugger

debugger = AnnouncerDebugger(plugin_instance)

# 创建真实场景的模拟数据
mock_tickets = [
    debugger.create_mock_ticket("10001", "1001", "new", "你关注的剧目", "2025-10-20", "A区", "100"),
]
mock_result = debugger.create_mock_result(mock_tickets)

# 测试特定用户
messages = debugger.test_generate_announce_text(mock_result, "用户QQ号")
```

---

## 常见问题解答

### Q1: 定时任务在运行，但从不收到通知？

**排查点：**
1. 检查 `Hlq.compare_to_database_async()` 是否总是返回空的 `categorized`
2. 检查是否因为数据异常被拦截（代码中有 `if len(categorized["新"]) >= 400` 的保护逻辑）
3. 检查时间间隔是否太长，用户已经通过其他方式知道上新

**解决方案：**
- 减小检测间隔（当前是 `scheduled_task_time` 配置）
- 添加日志查看每次检测的结果

### Q2: 模拟测试能生成消息，但真实场景不行？

**问题在：** 数据比对环节

**排查：**
1. 手动 `/refresh` 后查看日志
2. 检查 `HulaquanDataManager.py` 中的 `compare_to_database_async` 方法
3. 可能是网络问题、API变化、或数据格式问题

### Q3: 消息生成了，但用户没收到？

**可能原因：**
1. API 发送失败（`retcode != 0`）
2. 用户屏蔽了机器人
3. 消息被风控

**排查：**
- 查看日志中的 `retcode`
- 代码中有 `if r['retcode'] == 1200` 的处理（用户不存在）

### Q4: 只有部分用户收不到？

**排查：**
- 使用 `/debug通知 user` 查看该用户的设置
- 检查该用户是否在好友列表中
- 查看日志中该用户的消息发送情况

---

## 模拟真实上新场景

如果想完整测试整个流程，可以：

### 方法1：修改代码，注入模拟数据

在 `on_hulaquan_announcer` 中临时添加：

```python
async def on_hulaquan_announcer(self, test=False, manual=False, announce_admin_only=False):
    # ... 原有代码获取 result
    
    # 【测试用】注入模拟上新数据
    if test:
        result["categorized"]["new"].append("99999")
        result["tickets"]["99999"] = {
            "id": "99999",
            "event_id": "9999",
            "categorized": "new",
            "message": "[测试] 测试剧目 | 2025-10-20 | A区 | ¥100"
        }
        result["events"]["9999"] = ["99999"]
        result["events_prefixes"]["9999"] = "【测试剧目】"
    
    # ... 继续原有逻辑
```

然后调用：
```python
await plugin.on_hulaquan_announcer(test=True, announce_admin_only=True)
```

### 方法2：使用 debug_announcer.py

```python
from plugins.Hulaquan.debug_announcer import run_debug_tests

# 完整调试流程
await run_debug_tests(plugin_instance)
```

---

## 推荐的调试顺序

```
1. /debug通知 check     → 确认任务运行
2. /debug通知 user      → 确认用户设置
3. /debug通知 mock      → 测试消息生成
4. /refresh             → 手动触发刷新
5. 查看日志             → 分析问题点
6. 代码层面调试         → 深入排查
```

---

## 快速检查清单

- [ ] 定时任务是否在运行？
- [ ] 用户全局模式是否为 1/2/3？
- [ ] 模拟测试能否生成消息？
- [ ] `Hlq.compare_to_database_async()` 是否返回数据？
- [ ] 日志中是否有错误信息？
- [ ] API 发送是否成功（retcode=0）？
- [ ] 用户是否在好友列表中？
- [ ] 检测间隔是否合理？

---

## 联系支持

如果以上方法都无法解决问题，请提供：
1. `/debug通知 check` 的输出
2. `/debug通知 user` 的输出
3. `/debug通知 mock` 的输出
4. 最近的日志文件（`logs/bot.log`）
5. 具体的场景描述（什么时候应该收到但没收到）
