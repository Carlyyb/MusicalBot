"""旧 JSON 管理器的兼容适配层入口。"""
from .alias_manager import add_alias, find_by_alias, record_no_response
from .hlq_manager import get_event_tickets
from .users_manager import add_event_subscribe, has_permission, list_subs, subscribe_tickets

__all__ = [
    "add_alias",
    "find_by_alias",
    "record_no_response",
    "get_event_tickets",
    "subscribe_tickets",
    "add_event_subscribe",
    "list_subs",
    "has_permission",
]
