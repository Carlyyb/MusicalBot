from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class User:
    """
    用户核心数据结构
    """
    user_id: str
    nickname: Optional[str] = None
    is_admin: bool = False
    attention_to_hulaquan: int = 0  # 0-3, 通知模式
    subscribed_events: List[str] = field(default_factory=list)  # event_id 列表
    subscribed_tickets: List[str] = field(default_factory=list)  # ticket_id 列表
    contact: Optional[str] = None
