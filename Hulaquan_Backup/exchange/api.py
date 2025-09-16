"""
api.py
对外接口，供主bot或UI调用
"""
from .manager import ExchangeManager
from .matcher import ExchangeMatcher

exchange_manager = ExchangeManager()
exchange_matcher = ExchangeMatcher(exchange_manager)

def create_exchange_request(user_id, offer_items, want_items, conditions=None, contact=None):
    """
    创建并存储盘票请求，返回请求ID
    """
    from .models import ExchangeRequest
    req = ExchangeRequest(user_id, offer_items, want_items, conditions, contact)
    req_id = exchange_manager.add_request(req)
    return req_id

def get_user_requests(user_id):
    """
    获取某用户的所有盘票请求
    """
    return exchange_manager.find_by_user(user_id)

def match_for_user(user_id):
    """
    查找用户可达成的盘票链路
    """
    return exchange_matcher.find_exchange_chains(user_id)

def get_all_requests():
    """
    获取所有盘票请求
    """
    return exchange_manager.all_requests()

def remove_exchange_request(req_id):
    """
    删除指定ID的盘票请求
    """
    return exchange_manager.remove_request(req_id)