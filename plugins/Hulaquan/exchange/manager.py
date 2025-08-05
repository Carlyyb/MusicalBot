"""
manager.py
负责盘票请求的存储、增删查改，持久化
"""
from typing import List
from .models import ExchangeRequest, ExchangeItem, TicketItem, CashItem, GoodsItem
from plugins.AdminPlugin.BaseDataManager import BaseDataManager

EXCHANGE_REQUESTS = "exchange_requests"

class ExchangeManager(BaseDataManager):
    """
    盘票请求管理器，持久化存储所有请求
    """
    def __init__(self, file_path=None):
        super().__init__(file_path)

    def on_load(self):
        self.data.setdefault(EXCHANGE_REQUESTS, {})  # {request_id: dict}
        self.data.setdefault("latest_id", 1000000)

    def new_id(self):
        self.data["latest_id"] += 1
        return str(self.data["latest_id"])

    def add_request(self, req: ExchangeRequest):
        req_id = self.new_id()
        # 内存中存放实例，保存时序列化
        self.data[EXCHANGE_REQUESTS][req_id] = req
        return req_id

    def remove_request(self, req_id):
        if req_id in self.data[EXCHANGE_REQUESTS]:
            del self.data[EXCHANGE_REQUESTS][req_id]
            return True
        return False


    def find_by_user(self, user_id):
        return [r for r in self.data[EXCHANGE_REQUESTS].values() if hasattr(r, 'user_id') and r.user_id == user_id]

    def all_requests(self):
        # return -> 
        result: List[ExchangeRequest]  = [r for r in self.data[EXCHANGE_REQUESTS].values() if hasattr(r, 'user_id')]
        return result

    def _serialize_items(self, items):
        # 递归序列化嵌套结构
        if isinstance(items, list):
            return [self._serialize_items(i) for i in items]
        elif hasattr(items, 'to_dict'):
            return items.to_dict()
        else:
            return items

    def _serialize_request(self, req: ExchangeRequest):
        # 递归序列化ExchangeRequest对象
        return {
            'user_id': req.user_id,
            'offer_items': self._serialize_items(req.offer_items),
            'want_items': self._serialize_items(req.want_items),
            'conditions': req.conditions,
            'contact': req.contact
        }

    async def save(self, on_close=False):
        # 保存时序列化所有实例
        serializable_data = {}
        for req_id, req in self.data[EXCHANGE_REQUESTS].items():
            if hasattr(req, 'user_id'):
                serializable_data[req_id] = self._serialize_request(req)
            else:
                serializable_data[req_id] = req
        backup = self.data[EXCHANGE_REQUESTS]
        self.data[EXCHANGE_REQUESTS] = serializable_data
        result = await super().save(on_close=on_close)
        self.data[EXCHANGE_REQUESTS] = backup
        return result

    # 可扩展：反序列化、编辑、查找等方法