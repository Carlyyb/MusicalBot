"""
matcher.py
负责盘票链路的匹配算法伪代码
"""
from .models import ExchangeRequest, ExchangeItem, TicketItem
from .manager import ExchangeManager

class ExchangeMatcher:
    def __init__(self, manager: ExchangeManager):
        self.manager: ExchangeManager = manager

    def find_exchange_chains(self, target_user_id, max_depth=6):
        """
        递归查找target_user_id能达成的盘票链路，返回所有可行链路

        设计说明：
        - 每个ExchangeRequest的offer_items/want_items支持嵌套：
            - 外层list为OR，内层list为AND
            - 例如 want_items = [itemA, [itemB, itemC]]
              表示“要itemA”或“要itemB和itemC一起”
        - 匹配时：
            - offer_items的每个元素（item或[item,...]）都可作为一次“可出”
            - want_items同理
            - 匹配AND时，需一次性满足全部item
        - 匹配链路：
            - 递归查找，允许多层中转
            - 返回所有可行链路
        - 返回格式：
            [
                [ (user_id1, offer_item, want_item), (user_id2, offer_item, want_item), ... ],
                ...
            ]
            offer_item/want_item为dict或list[dict]
        - 兼容原有功能：如无嵌套则等价于OR
        """
        all_requests = self.manager.all_requests()
        user_requests = [r for r in all_requests if r['user_id'] == target_user_id]
        if not user_requests:
            return []
        want_items = []
        for req in user_requests:
            want_items.extend(req['want_items'])

        def item_match(offer: ExchangeItem, want: ExchangeItem):
            is_multiple_offer = isinstance(offer, list)
            is_multiple_want = isinstance(want, list)
            if is_multiple_offer and is_multiple_want:
                # 都是AND
                return
            if not is_multiple_want and not is_multiple_offer:
                # 都是单个item
                typ_offer, typ_want = offer.type, want.type
                if typ_offer == typ_want == "ticket":
                    typ_want: TicketItem
                    typ_offer: TicketItem
                    if typ_offer.event_id == typ_want.event_id:
                    
                else:
                    return True
                
            
            # return item1['type'] == item2['type'] and item1.get('title', item1.get('name')) == item2.get('title', item2.get('name'))

        results = []

        def dfs(chain, used_users, current_wants, depth):
            if depth > max_depth:
                return
            for req in all_requests:
                uid = req['user_id']
                if uid in used_users:
                    continue
                for offer in req['offer_items']:
                    for want in current_wants:
                        # offer是否能满足want
                        if item_match(offer, want):
                            new_chain = chain + [(uid, offer, want)]
                            if target_user_id == uid:
                                results.append(new_chain)
                                continue
                            dfs(new_chain, used_users | {uid}, req['want_items'], depth+1)

        dfs(chain=[(target_user_id, None, w) for w in want_items], used_users={target_user_id}, current_wants=want_items, depth=1)
        return results