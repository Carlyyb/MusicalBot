"""
扩展的数据类型定义
添加了详细的数据结构内容说明和具体格式
"""

from typing import Dict, List, Optional, Union, Any, Tuple, Literal
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


# 详细的数据结构类型注解

# 基础类型别名 - 包含具体内容说明
EventId = str  # 事件ID，例如: "3863", "12345"
TicketId = str  # 票务ID，例如: "31777", "32808"
UserId = str   # 用户ID，例如: "1234567890", "user123"
SearchName = str  # 搜索名称，例如: "连壁", "哈姆雷特"
Alias = str    # 别名，例如: "丽兹", "连璧"

# 事件搜索结果格式
EventSearchItem = Tuple[EventId, str]  # [EventID, EventName] 例如: ("3863", "《连壁》")
EventSearchResult = List[EventSearchItem]  # [[EventID, EventName], ...] 例如: [("3863", "《连壁》"), ("3864", "《哈姆雷特》")]

# 票务详细信息字典格式
TicketDetailDict = Dict[str, Union[str, int, None]]
"""
票务详细信息字典结构示例:
{
    "id": "31777",
    "event_id": "3863",
    "title": "《连壁》07-19 20:00￥199（原价￥299) 学生票",
    "start_time": "2025-07-19 20:00:00",
    "end_time": "2025-07-19 21:00:00",
    "status": "active",  # "active" | "pending" | "expired"
    "create_time": "2025-06-11 11:06:13",
    "ticket_price": 199,
    "total_ticket": 14,
    "left_ticket_count": 2,
    "left_days": 25,
    "valid_from": "2025-07-19 18:00:00",
    "cast": [{"artist": "韩冰儿", "role": "连壁"}, {"artist": "胥子含", "role": "哈姆雷特"}],
    "city": "上海"
}
"""

# 事件信息字典格式
EventInfoDict = Dict[str, Any]
"""
事件信息字典结构示例:
{
    "id": "3863",
    "title": "《连壁》",
    "location": "上海",
    "start_time": "2025-07-19 00:00:00",
    "end_time": "2025-08-15 23:59:59",
    "update_time": "2025-07-10 15:30:00",
    "deadline": "2025-08-15 23:59:59",
    "create_time": "2025-06-01 10:00:00",
    "ticket_details": {
        "31777": TicketDetailDict,
        "31778": TicketDetailDict,
        ...
    }
}
"""

# 数据比较结果格式
CompareResultDict = Dict[str, Any]
"""
数据比较结果字典结构示例:
{
    "events": {
        "3863": ["31777", "31778"],  # EventID -> [TicketID, TicketID, ...]
        "3864": ["31779"]
    },
    "events_prefixes": {
        "3863": "剧名: 《连壁》\n购票链接: https://...\n更新时间: 2025-07-10 15:30:00",
        "3864": "剧名: 《哈姆雷特》\n购票链接: https://...\n更新时间: 2025-07-10 15:30:00"
    },
    "categorized": {
        "new": ["31777", "31778"],      # 新上架票务ID列表
        "add": ["31779"],               # 补票ID列表
        "pending": [],                  # 待开票ID列表
        "return": ["31780"],            # 回流票ID列表
        "sold": ["31781"],              # 售罄票ID列表
        "back": ["31782"]               # 增票ID列表
    },
    "tickets": {
        "31777": {
            "message": "✨《连壁》07-19 19:30￥199（原价￥299) 学生票 余票2/14 韩冰儿 胥子含",
            "categorized": "new",
            "event_id": "3863"
        }
    },
    "prefix": {
        "new": "🆕上新",
        "add": "🟢补票",
        "return": "♻️回流",
        "sold": "➖票减",
        "back": "➕票增",
        "pending": "⏲️开票"
    }
}
"""

# 别名数据结构格式
AliasDataDict = Dict[str, Dict[str, Union[str, List[str], int]]]
"""
别名数据字典结构示例:
{
    "alias_to_event": {
        "丽兹": "3863",           # 别名 -> EventID
        "连璧": "3863",
        "哈姆": "3864"
    },
    "event_to_names": {
        "3863": ["连壁", "Lizzie", "丽兹"],  # EventID -> [搜索名称列表]
        "3864": ["哈姆雷特", "Hamlet", "哈姆"]
    },
    "name_to_alias": {
        "连壁": "3863",           # 搜索名称 -> EventID
        "Lizzie": "3863",
        "哈姆雷特": "3864"
    },
    "no_response": {
        "丽兹:Lizzie": 0,         # "别名:搜索名称" -> 无响应次数
        "哈姆:Hamlet": 1
    }
}
"""

# Repo记录格式
RepoRecordDict = Dict[str, Union[str, Dict[str, Any]]]
"""
Repo记录字典结构示例:
{
    "report_id": "1001",
    "user_id": "1234567890",
    "event_id": "3863",
    "title": "《连壁》",
    "date": "2025-07-19",
    "seat": "A区1排1座",
    "price": "199",              # 实付价格
    "payable": "299",            # 原价
    "content": "视野很好，音效清晰",
    "category": "学生票",         # "学生票" | "全价票" | "其他"
    "create_time": "2025-07-10 15:30:00",
    "img": "https://example.com/image.jpg",
    "report_error_details": {
        "count": 0,              # 错误报告次数
        "reporters": [],         # 报告用户ID列表
        "details": [            # 详细错误信息
            {
                "user": "user123",
                "content": "座位信息有误",
                "time": "2025-07-11 10:00:00"
            }
        ]
    }
}
"""

# 扫剧演出信息格式
SaojuShowDict = Dict[str, Union[str, List[Dict[str, str]]]]
"""
扫剧演出信息字典结构示例:
{
    "musical": "《连壁》",
    "time": "19:30",
    "city": "上海",
    "date": "2025-07-19",
    "venue": "上海大剧院",
    "price": "199-799",
    "url": "https://example.com/ticket",
    "cast": [
        {"artist": "韩冰儿", "role": "连壁"},
        {"artist": "胥子含", "role": "哈姆雷特"}
    ]
}
"""

# 票务状态更新类型
TicketUpdateStatus = Literal["new", "add", "pending", "return", "sold", "back"]

# 票务验证结果格式
TicketVerificationResult = Tuple[List[TicketId], List[TicketId]]
# (有效票务ID列表, 无效票务ID列表) 例如: (["31777", "31778"], ["invalid1", "invalid2"])

# 事件名称解析结果格式
EventNameParseResult = Tuple[Optional[EventId], Optional[str]]
# (EventID或None, 错误消息或None) 例如: ("3863", None) 或 (None, "未找到该剧目")

# 多事件名称解析结果格式（当找到多个匹配时）
MultiEventParseResult = Union[EventNameParseResult, Tuple[List[EventId], str]]
# 单个结果: ("3863", None)
# 多个结果: (["3863", "3864"], "找到多个匹配的剧名，请重新以唯一的关键词查询：\n1. 《连壁》\n2. 《哈姆雷特》")

# 分页显示结果格式
PaginatedResult = List[str]  # 格式化后的字符串列表，每个字符串代表一页内容


@dataclass
class DetailedEventInfo:
    """
    详细的事件信息数据类
    包含完整的票务和元数据信息
    """
    id: EventId  # "3863"
    title: str   # "《连壁》"
    location: Optional[str] = None  # "上海"
    start_time: Optional[str] = None  # "2025-07-19 00:00:00"
    end_time: Optional[str] = None    # "2025-08-15 23:59:59"
    update_time: Optional[str] = None # "2025-07-10 15:30:00"
    deadline: Optional[str] = None    # "2025-08-15 23:59:59"
    create_time: Optional[str] = None # "2025-06-01 10:00:00"

    # 票务详情映射: TicketID -> TicketDetailDict
    ticket_details: Optional[Dict[TicketId, TicketDetailDict]] = None


@dataclass
class DetailedTicketInfo:
    """
    详细的票务信息数据类
    包含演出时间、价格、卡司等完整信息
    """
    id: TicketId      # "31777"
    event_id: EventId # "3863"
    title: str        # "《连壁》07-19 19:30￥199（原价￥299) 学生票"
    start_time: Optional[str] = None      # "2025-07-19 19:30:00"
    end_time: Optional[str] = None        # "2025-07-19 21:00:00"
    status: str = "active"                # "active" | "pending" | "expired"
    create_time: Optional[str] = None     # "2025-06-11 11:06:13"
    ticket_price: Optional[int] = None    # 199
    total_ticket: Optional[int] = None    # 14
    left_ticket_count: Optional[int] = None  # 2
    left_days: Optional[int] = None       # 25
    valid_from: Optional[str] = None      # "2025-07-19 18:00:00"

    # 演员信息: [{"artist": "演员名", "role": "角色名"}, ...]
    cast: Optional[List[Dict[str, str]]] = None
    city: Optional[str] = None            # "上海"
    update_status: Optional[TicketUpdateStatus] = None  # "new" | "add" | ...


# 高级组合类型
EventsMapping = Dict[EventId, DetailedEventInfo]  # EventID -> 完整事件信息
TicketsMapping = Dict[TicketId, DetailedTicketInfo]  # TicketID -> 完整票务信息
EventTicketsMapping = Dict[EventId, TicketsMapping]  # EventID -> (TicketID -> 票务信息)