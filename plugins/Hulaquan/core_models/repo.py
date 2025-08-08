from dataclasses import dataclass
from typing import Optional

@dataclass
class Repo:
    """
    学生票repo（用户上传的票据记录）
    """
    repo_id: str
    event_id: str
    event_title: str
    user_id: str
    date: str
    seat: str
    price: float
    category: str
    payable: Optional[float] = None
    content: Optional[str] = None
    img: Optional[str] = None
    create_time: Optional[str] = None
