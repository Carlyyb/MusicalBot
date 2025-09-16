



from abc import ABC, abstractmethod
from typing import List

class ExchangeItem(ABC):
    """
    资源抽象基类，可为票据、现金、物品
    """
    @abstractmethod
    def to_dict(self):
        pass

class TicketItem(ExchangeItem):
    def __init__(self, 
                 title: str, 
                 date: str,
                 seat: str, 
                 cast: str=None,
                 event_id: str=None,
                 orig_price: int=None, 
                 sell_price: int=None, 
                 note: str=None, 
                 channel: str=None):
        self.type = "ticket"
        self.title = title
        self.date = date
        self.seat = seat
        self.cast = cast
        self.event_id = event_id
        self.orig_price = orig_price
        self.sell_price = sell_price
        self.note = note
        self.channel = channel
    def to_dict(self):
        return {
            'type': 'ticket',
            'title': self.title,
            'date': self.date,
            'seat': self.seat,
            'cast': self.cast,
            'orig_price': self.orig_price,
            'sell_price': self.sell_price,
            'note': self.note,
            'channel': self.channel
        }

class CashItem(ExchangeItem):
    def __init__(self, 
                 amount: int, 
                 currency: str='CNY', 
                 note: str=None
                 ):
        self.type = "cash"
        self.amount = amount
        self.currency = currency
        self.note = note
    def to_dict(self):
        return {
            'type': 'cash',
            'amount': self.amount,
            'currency': self.currency,
            'note': self.note
        }

class GoodsItem(ExchangeItem):
    def __init__(self, 
                 name: str, 
                 quantity: str=None, 
                 note: str=None
                 ):
        self.type = "goods"
        self.name = name
        self.quantity = quantity
        self.note = note
    def to_dict(self):
        return {
            'type': 'goods',
            'name': self.name,
            'quantity': self.quantity,
            'note': self.note
        }

class ExchangeRequest:
    """
    用户的盘票请求，支持多种组合
    """
    
    def __init__(self, 
                 user_id: str, 
                 offer_items: List[ExchangeItem|List[ExchangeItem]], 
                 want_items: List[ExchangeItem|List[ExchangeItem]] , 
                 conditions: str=None, 
                 contact: str=None):
        self.user_id = user_id
        self.offer_items: List[ExchangeItem|List[ExchangeItem]] = offer_items      # List[ExchangeItem] 或 List[List[ExchangeItem]]
        self.want_items: List[ExchangeItem|List[ExchangeItem]] = want_items        # List[ExchangeItem] 或 List[List[ExchangeItem]]
        self.conditions = conditions or {}
        self.contact = contact
        # 支持嵌套列表
        # - 外层list为OR，内层list为AND
        # - 例如：
        #     offer_items = [itemA, [itemB, itemC]]
        #     表示可单独出itemA，或必须一起出itemB和itemC
        # - want_items同理
        # - 兼容原有功能：如无嵌套则等价于OR