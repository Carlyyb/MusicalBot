"""
核心数据类型定义
用于数据管理模块的类型注解和数据验证
"""

from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TicketStatus(Enum):
    """票务状态枚举"""
    ACTIVE = "active"
    PENDING = "pending"
    EXPIRED = "expired"


class UpdateStatus(Enum):
    """更新状态枚举"""
    NEW = "new"
    ADD = "add"
    PENDING = "pending"
    RETURN = "return"
    SOLD = "sold"
    BACK = "back"


@dataclass
class EventInfo:
    """呼啦圈事件基本信息"""
    id: str
    title: str
    location: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    update_time: Optional[str] = None
    deadline: Optional[str] = None
    create_time: Optional[str] = None


@dataclass
class TicketInfo:
    """票务详细信息"""
    id: str
    event_id: str
    title: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: TicketStatus = TicketStatus.ACTIVE
    create_time: Optional[str] = None
    ticket_price: Optional[int] = None
    total_ticket: Optional[int] = None
    left_ticket_count: Optional[int] = None
    left_days: Optional[int] = None
    valid_from: Optional[str] = None
    cast: Optional[List[Dict[str, str]]] = None
    city: Optional[str] = None
    update_status: Optional[UpdateStatus] = None


@dataclass
class AliasData:
    """别名系统数据结构"""
    alias_to_event: Dict[str, str]
    event_to_names: Dict[str, List[str]]
    name_to_alias: Dict[str, str]
    no_response: Dict[str, int]


@dataclass
class EventSearchResult:
    """事件搜索结果"""
    event_id: str
    event_title: str
    confidence: float = 1.0  # 匹配置信度


@dataclass
class CompareResult:
    """数据比较结果"""
    events: Dict[str, List[str]]  # event_id -> [ticket_id, ...]
    events_prefixes: Dict[str, str]  # event_id -> message_prefix
    categorized: Dict[str, List[str]]  # status -> [ticket_id, ...]
    tickets: Dict[str, Dict[str, Any]]  # ticket_id -> ticket_info
    prefix: Dict[str, str]  # status -> emoji_prefix


@dataclass
class SaojuEventInfo:
    """扫剧网站事件信息"""
    musical: str
    time: str
    city: str
    date: str
    cast: List[Dict[str, str]]


@dataclass
class RepoRecord:
    """学生票座位记录"""
    report_id: str
    user_id: str
    event_id: str
    title: str
    date: str
    seat: str
    price: str
    content: str
    category: str
    payable: str
    create_time: str
    img: Optional[str] = None
    report_error_details: Dict[str, Any] = None


# 类型别名定义
EventId = str
TicketId = str
UserId = str
SearchName = str
Alias = str

# 常用的复合类型
EventsDict = Dict[EventId, EventInfo]
TicketsDict = Dict[TicketId, TicketInfo]
EventTicketsDict = Dict[EventId, TicketsDict]
SearchResults = List[EventSearchResult]
ComparisonData = Dict[EventId, Dict[str, List[TicketInfo]]]