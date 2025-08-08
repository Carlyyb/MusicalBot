from ..api.user_api import (
    register_user, get_user, subscribe_ticket, subscribe_event, unsubscribe_ticket, unsubscribe_event
)

def handle_register_user(user_id: str, contact: str = None):
    user = register_user(user_id, contact)
    return f"用户 {user_id} 注册成功。"

def handle_subscribe_ticket(user_id: str, ticket_id: str, mode: int):
    subscribe_ticket(user_id, ticket_id, mode)
    return f"用户 {user_id} 订阅票 {ticket_id} 成功。"

def handle_subscribe_event(user_id: str, event_id: str, mode: int):
    subscribe_event(user_id, event_id, mode)
    return f"用户 {user_id} 订阅演出 {event_id} 成功。"

def handle_unsubscribe_ticket(user_id: str, ticket_id: str):
    unsubscribe_ticket(user_id, ticket_id)
    return f"用户 {user_id} 取消订阅票 {ticket_id} 成功。"

def handle_unsubscribe_event(user_id: str, event_id: str):
    unsubscribe_event(user_id, event_id)
    return f"用户 {user_id} 取消订阅演出 {event_id} 成功。"
