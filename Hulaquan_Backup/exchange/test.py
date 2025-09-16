"""
test.py
盘票链路匹配功能测试用例模板
"""
from .models import TicketItem, CashItem, GoodsItem, ExchangeRequest
from .manager import ExchangeManager
from .matcher import ExchangeMatcher

if __name__ == "__main__":
    # 构造测试数据
    manager = ExchangeManager(file_path=None)
    # 清空数据
    manager.data['exchange_requests'] = {}
    manager.data['latest_id'] = 1000

    # 用户A想要B剧，出A剧
    reqA = ExchangeRequest(
        user_id='A',
        offer_items=[TicketItem('剧A', '2025-08-10', '1排1座')],
        want_items=[TicketItem('剧B', '2025-08-12', '2排2座')],
        contact='A联系方式'
    )
    # 用户B想要C剧，出B剧
    reqB = ExchangeRequest(
        user_id='B',
        offer_items=[TicketItem('剧B', '2025-08-12', '2排2座')],
        want_items=[TicketItem('剧C', '2025-08-15', '3排3座')],
        contact='B联系方式'
    )
    # 用户C想要A剧，出C剧
    reqC = ExchangeRequest(
        user_id='C',
        offer_items=[TicketItem('剧C', '2025-08-15', '3排3座')],
        want_items=[TicketItem('剧A', '2025-08-10', '1排1座')],
        contact='C联系方式'
    )

    manager.add_request(reqA)
    manager.add_request(reqB)
    manager.add_request(reqC)

    matcher = ExchangeMatcher(manager)
    chains = matcher.find_exchange_chains('A')
    print("A的可达成链路:")
    for chain in chains:
        print("---")
        for uid, offer, want in chain:
            print(f"用户{uid} 可出: {offer}，满足: {want}")
