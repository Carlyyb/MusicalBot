from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Ticket:
    """
    音乐剧票据的核心数据结构
    """
    ticket_id: str
    event_id: str
    event_title: str
    date: str
    seat: str
    price: float
    category: str = "学生票"
    payable: Optional[float] = None
    owner_id: Optional[str] = None
    status: str = "active"  # active, pending, sold, etc.
    create_time: Optional[str] = None
    note: Optional[str] = None
    img: Optional[str] = None
