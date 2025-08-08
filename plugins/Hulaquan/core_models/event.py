from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Event:
    """
    剧目/演出事件的核心数据结构
    """
    event_id: str
    title: str
    location: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    update_time: Optional[str] = None
    deadline: Optional[str] = None
    create_time: Optional[str] = None
    tickets: List[str] = field(default_factory=list)  # ticket_id 列表
