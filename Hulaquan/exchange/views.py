
"""
views.py
UI/命令行/机器人消息接口伪代码
"""
from .api import create_exchange_request, get_user_requests, match_for_user

def user_submit_exchange(user_id, offer_items, want_items, contact):
    """
    offer_items/want_items: List[ExchangeItem]对象
    contact: str
    """
    req_id = create_exchange_request(user_id, offer_items, want_items, contact=contact)
    return f"提交成功，您的请求ID为: {req_id}"

def user_query_matches(user_id):
    """
    查询可达成的链路，返回格式化字符串
    """
    chains = match_for_user(user_id)
    if not chains:
        return "暂未找到可达成的盘票链路"
    lines = []
    for chain in chains:
        s = []
        for uid, offer, want in chain:
            if offer is None:
                s.append(f"用户{uid} 需求: {want}")
            else:
                s.append(f"用户{uid} 可出: {offer}，满足: {want}")
        lines.append(" -> ".join(s))
    return "\n---\n".join(lines)