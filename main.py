"""
入口脚本: 在不改动 ncatbot 源码前提下，对新版 NapCat 的 WS 差异做兼容层。

解决的问题（对应你总结的根因里 4 / 5 / 6 / 7 点）：
1. /event 路径不一定存在：支持自动探测 root 与 /event。
2. token 可能放在 header 或 query：增加两种模式（默认双探测）。
3. 首帧消息格式可能是 object / array / string：增加 auto 识别与日志提示。
4. 关闭本地 NapCat CLI 管理行为：通过 remote_mode & enable_webui_interaction=False 避免误判回退。

使用方式（环境变量，可选）：
  NCATBOT_WS_EVENT_PATH   指定事件路径（不写则自动探测 root 与 /event）
  NCATBOT_WS_TOKEN_MODE   header|query|both   （默认 both）
  NCATBOT_MESSAGE_FORMAT  auto|object|array|string  （默认 auto）
  NCATBOT_FORCE_WS_URI    如果想覆盖 requirements 里默认配置，可写完整 ws://host:port[/path]

运行时会打印一次兼容层配置快照，出现格式不匹配时会给出前缀样本，方便排障。
"""

# ========= 导入必要模块 ==========
from ncatbot.core import BotClient, GroupMessage, PrivateMessage, BaseMessage
from ncatbot.utils import get_log, config

import os
import json
import asyncio
import traceback
import websockets  # 依赖由 ncatbot 已经引入
from typing import Optional, List

# ---------- 兼容层：Monkey Patch Websocket ----------
try:
    from ncatbot.adapter.net import connect as _nc_connect
    from ncatbot.adapter.nc import launcher as _nc_launcher
except ImportError:  # 理论不触发
    _nc_connect = None
    _nc_launcher = None

_log = get_log()

def _patch_websocket():
    if _nc_connect is None:
        _log.warning("未找到 ncatbot.adapter.net.connect，跳过兼容层打补丁")
        return

    # 已经打过补丁就不再重复
    if getattr(_nc_connect.Websocket, "__patched__", False):
        return

    def _load_runtime_ws_token() -> str:
        """尝试自动读取 NapCat websocketServers token（新版可能重启刷新）。
        优先级: ENV:NCATBOT_RUNTIME_WSTOKEN > onebot11_* 文件 > config.ws_token
        """
        env_tok = os.getenv("NCATBOT_RUNTIME_WSTOKEN")
        if env_tok:
            return env_tok.strip()
        # 允许用户指定文件路径
        token_file = os.getenv("NCATBOT_ONEBOT_CONFIG_FILE")
        candidate_files: List[str] = []
        if token_file and os.path.exists(token_file):
            candidate_files.append(token_file)
        else:
            # 自动扫描常见路径 napcat/config/onebot11_*.json
            base_dir = os.path.join(os.getcwd(), "napcat", "config")
            if os.path.isdir(base_dir):
                for fn in os.listdir(base_dir):
                    if fn.startswith("onebot11_") and fn.endswith('.json'):
                        candidate_files.append(os.path.join(base_dir, fn))
        for fp in candidate_files:
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                servers = data.get("network", {}).get("websocketServers", [])
                if servers and isinstance(servers, list):
                    tok = servers[0].get("token") or ""
                    if tok:
                        _log.info("[NapCatCompat] 从文件加载 WS token: %s", fp)
                        return tok
            except Exception as e:
                _log.debug("[NapCatCompat] 读取 token 文件失败 %s: %s", fp, e)
        # fallback
        return config.ws_token or ""

    class PatchedWebsocket(_nc_connect.Websocket):  # 继承原类，覆盖需要的逻辑
        __patched__ = True

        def __init__(self, client):  # 基本沿用，但改 URI 构建策略
            self.client = client

            # ========== 读取环境变量 / 配置 ==========
            env_force_uri = os.getenv("NCATBOT_FORCE_WS_URI")
            if env_force_uri:
                # 允许直接写完整地址（包含 path）
                base_uri = env_force_uri.rstrip("/")
                config.ws_uri = base_uri  # 覆盖内部 config，便于日志
            else:
                base_uri = config.ws_uri.rstrip("/")

            event_path_env = os.getenv("NCATBOT_WS_EVENT_PATH", "").strip()
            token_mode = os.getenv("NCATBOT_WS_TOKEN_MODE", "both").lower()
            message_format_mode = os.getenv("NCATBOT_MESSAGE_FORMAT", "auto").lower()

            # token（ws_token）优先级：ENV:NCATBOT_RUNTIME_WSTOKEN > config.ws_token > 空
            runtime_token = _load_runtime_ws_token()
            # 动态写回 config 便于 API 请求 header 复用
            if runtime_token:
                config.ws_token = runtime_token
            # 构建候选路径
            candidate_paths = []
            if event_path_env:
                p = event_path_env if event_path_env.startswith('/') else '/' + event_path_env
                candidate_paths.append(p)
            else:
                # 自动探测常规顺序：root 优先，再 fallback /event
                candidate_paths.extend(["", "/event"])  # 空表示 root

            self._token = runtime_token
            self._token_mode = token_mode  # header / query / both
            self._message_format_mode = message_format_mode  # auto|object|array|string
            self._base_uri = base_uri
            self._candidate_full_urls = []

            for p in candidate_paths:
                full = base_uri + p
                if token_mode in {"query", "both"} and runtime_token:
                    sep = '&' if ('?' in full) else '?'
                    full_with_query = f"{full}{sep}token={runtime_token}"
                    self._candidate_full_urls.append(full_with_query)
                self._candidate_full_urls.append(full)

            # 去重保持顺序
            seen = set()
            ordered = []
            for u in self._candidate_full_urls:
                if u not in seen:
                    seen.add(u)
                    ordered.append(u)
            self._candidate_full_urls = ordered

            # Header 构建
            self._header = {"Content-Type": "application/json"}
            if runtime_token and token_mode in {"header", "both"}:
                self._header["Authorization"] = f"Bearer {runtime_token}"

            _log.info(
                "[NapCatCompat] 配置快照 ws_uri=%s candidates=%s token_mode=%s msg_format=%s token_len=%s",
                base_uri,
                self._candidate_full_urls,
                self._token_mode,
                self._message_format_mode,
                len(runtime_token),
            )

        # 覆盖消息分发，加 auto 识别
        def _dispatch_message_auto(self, raw_obj):
            # 期望 OneBot v11 event 是 object
            if isinstance(raw_obj, dict) and raw_obj.get("post_type"):
                return raw_obj
            # 如果是 list 并且第一个元素是 dict 且含有 post_type，取首元素
            if isinstance(raw_obj, list):
                if raw_obj and isinstance(raw_obj[0], dict) and raw_obj[0].get("post_type"):
                    return raw_obj[0]
                # 如果是 list 且像消息段数组（每项含 type / data），包装成一个伪事件（降级兼容）
                if raw_obj and isinstance(raw_obj[0], dict) and {"type", "data"} <= set(raw_obj[0].keys()):
                    return {
                        "post_type": "message",
                        "message_type": "group",  # 无法推断，默认 group，可后续外部过滤
                        "message": raw_obj,
                        "raw_message": "".join(
                            seg.get("data", {}).get("text", "") for seg in raw_obj if isinstance(seg, dict)
                        ),
                    }
            # string 情况尝试再 json 解析一层
            if isinstance(raw_obj, str):
                s = raw_obj.strip()
                if (s.startswith('{') and s.endswith('}')) or (s.startswith('[') and s.endswith(']')):
                    try:
                        return self._dispatch_message_auto(json.loads(s))
                    except Exception:
                        pass
            return None  # 交回上层做错误日志

        def on_message(self, message: dict):  # 保留原接口以兼容 ncatbot 逻辑
            return super().on_message(message)

        async def on_connect(self):  # 改为多候选尝试 + 格式自适应
            last_error: Optional[str] = None
            for url in self._candidate_full_urls:
                try:
                    _log.info("[NapCatCompat] 尝试连接候选 WS: %s", url)
                    async with websockets.connect(url, extra_headers=self._header, ping_interval=None) as ws:
                        _log.info("[NapCatCompat] 已连接: %s", url)
                        # 循环收消息
                        while True:
                            raw_text = await ws.recv()
                            try:
                                obj = json.loads(raw_text)
                            except Exception:
                                obj = raw_text  # 先保持原始

                            processed = None
                            if self._message_format_mode == "auto":
                                processed = self._dispatch_message_auto(obj)
                            elif self._message_format_mode == "object":
                                processed = obj if isinstance(obj, dict) else None
                            elif self._message_format_mode == "array":
                                # 如果是 list 直接包一层 shim
                                if isinstance(obj, list):
                                    processed = self._dispatch_message_auto(obj)
                            elif self._message_format_mode == "string":
                                if isinstance(obj, str):
                                    processed = self._dispatch_message_auto(obj)

                            if processed is None:
                                prefix = raw_text if isinstance(raw_text, str) else str(raw_text)
                                prefix = prefix[:160].replace('\n', ' ')
                                _log.error(
                                    "[NapCatCompat] 未识别的首帧/消息格式，prefix=%s (mode=%s)",
                                    prefix,
                                    self._message_format_mode,
                                )
                                continue  # 丢弃本条，等待下一条（不直接断开）

                            # 交给原 on_message
                            super().on_message(processed)
                except Exception as e:
                    last_error = f"{type(e).__name__}: {e}"
                    _log.warning("[NapCatCompat] 连接 %s 失败: %s", url, last_error)
                    continue
                # 正常退出（例如上层触发），跳出
                return
            # 全部失败，抛出以触发上层重试逻辑
            raise RuntimeError(f"所有候选 WS 均连接失败，最后错误: {last_error}")

    _nc_connect.Websocket = PatchedWebsocket  # 覆盖
    _log.info("[NapCatCompat] Websocket 兼容补丁已注入")

    # ---- 追加：跳过 ncatbot 原生 NapCat 启动/检查流程（避免 remote_mode 早退） ----
    if _nc_launcher and not getattr(_nc_launcher, "__patched_skip_launch__", False):
        def _patched_launch_napcat_service(*args, **kwargs):
            _log.info("[NapCatCompat] 已跳过 NapCat 启动管理流程 (launch_napcat_service monkey patched)")
            return True
        try:
            _nc_launcher.launch_napcat_service = _patched_launch_napcat_service
            _nc_launcher.__patched_skip_launch__ = True
            _log.info("[NapCatCompat] launcher.launch_napcat_service 已覆写")
        except Exception:
            _log.warning("[NapCatCompat] 覆写 launch_napcat_service 失败: %s", traceback.format_exc())


# 注入补丁并设置运行模式
_patch_websocket()
try:
    # 关闭 remote_mode，避免 launcher 中的远程模式早退；仍然禁止 webui 交互
    config.set_other_config(remote_mode=False, enable_webui_interaction=False, stop_napcat=False)
except Exception:
    _log.warning("[NapCatCompat] 设置 remote_mode 失败: %s", traceback.format_exc())

# 再次确保 launch_napcat_service 已被覆盖（如果前面因导入时机未成功）
if _nc_launcher and not getattr(_nc_launcher, "__patched_skip_launch__", False):
    def _patched_launch_napcat_service(*args, **kwargs):
        _log.info("[NapCatCompat] (late) 已跳过 NapCat 启动管理流程 launch_napcat_service")
        return True
    try:
        # 覆盖 launcher 模块函数
        _nc_launcher.launch_napcat_service = _patched_launch_napcat_service
        _nc_launcher.__patched_skip_launch__ = True
        # 同步覆盖 client 模块中已缓存的符号引用
        import ncatbot.core.client as _client_mod
        if getattr(_client_mod, 'launch_napcat_service', None) is not _patched_launch_napcat_service:
            _client_mod.launch_napcat_service = _patched_launch_napcat_service
            _log.info("[NapCatCompat] client.launch_napcat_service 引用已更新")
    except Exception:
        _log.warning("[NapCatCompat] (late) 覆写 launch_napcat_service 失败: %s", traceback.format_exc())



# ========== 创建 BotClient ==========
bot = BotClient()
_log = get_log()

HELLOWORDS = ["哈咯","Hi","测试","哈喽","Hello","剧剧"]
VERSION = "1.0"

# ========= 注册回调函数 ==========
@bot.group_event()
async def on_group_message(msg: GroupMessage):
    _log.info(msg)
    key, args = parse_args_of_messages(msg)
    if key:
        if any(word in key for word in HELLOWORDS):
            for m in hello_message():
                await bot.api.post_group_msg(msg.group_id, text=m)
    else:
        pass

@bot.private_event()
async def on_private_message(msg: PrivateMessage):
    _log.info(msg)

def hello_message():
    msg = []
    msg.append(f"""
    hihi我是剧剧机器人，致力于便捷广大zgyyj剧韭（划掉）查学生票查排期，目前只是初步实现，更多功能欢迎大家多多提议！\n
    当前版本：v{VERSION}\n
    目前已经实现的功能有：\n
    ✅1./hlq <剧名> <-i> <-c> 查某剧呼啦圈余票/数量/卡司\n
    -i表示忽略已售罄场次,-c表示显示排期对应卡司\n
    如：/hlq 丽兹 -c
    ✅2./上新 <0/1/2> 关注/取消关注呼啦圈上新推送\n
    /上新后的数字参数表示推送模式：0为不接受推送,1为只推送更新消息,2为推送每次检测结果（会推送无更新数据的结果）
    ✅3./date <日期> \n
    日期格式为 YYYY-MM-DD\n
    如：/date 2025-06-23\n
    ✅4./help 获取指令帮助文档
    """)
    msg.append(f"""
    ❗由于考虑到机器人服务的稳定性和快速性，有些数据更新可能并不及时，以下是各数据更新时间：\n
    ❗呼啦圈数据：默认五分钟查询一次\n
    ❗呼啦圈余票的卡司数据：12小时查询一次\n
    🟢有想要的功能可以在主包的小红书留言！欢迎nin来！
    🟡主包技术有限，机器人试运行初期可能会有各种问题烦请大家见谅，如有问题或体验问题欢迎多多反馈，实时数据以呼啦圈官网和扫剧（http://y.saoju.net/yyj/）为准。\n
    ~~最后祝大家有钱有票！剧场见！~~
    """)
    return msg
        
        
def parse_args_of_messages(message: BaseMessage):
    """
    解析消息中的参数
    :param message: BaseMessage 消息对象
    :return: 参数列表
    """
    args = []
    if message.raw_message:
        args = message.raw_message.split(' ')
        return args[0], args[1:] if len(args) > 1 else []
    return None, []

# ========== 启动 BotClient==========

if __name__ == "__main__":
    from ncatbot.utils import config
    # 设置 WebSocket 令牌
    #config.set_ws_token("ncatbot_ws_token")

    bot.run(bt_uin="3044829389", root="3022402752", enable_webui_interaction=False) # 这里写 Bot 的 QQ 号