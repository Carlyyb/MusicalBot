"""
重要函数的详细注解示例
包含完整的输入输出格式说明和具体数据结构内容
"""

from typing import Dict, List, Optional, Union, Any, Tuple
from .core_models.detailed_types import *


class AnnotatedHulaquanDataManager:
    """
    呼啦圈数据管理器 - 详细注解版本

    包含所有重要函数的详细输入输出格式说明
    """

    async def search_eventID_by_name_async(self, event_name: str) -> EventSearchResult:
        """
        根据事件名称异步搜索事件ID

        Args:
            event_name: 搜索的事件名称，例如: "连壁", "哈姆雷特", "Lizzie"

        Returns:
            EventSearchResult: 格式为 [[EventID, EventName], [EventID, EventName], ...]

            具体示例:
            - 单个匹配: [("3863", "《连壁》")]
            - 多个匹配: [("3863", "《连壁》"), ("3864", "《哈姆雷特》")]
            - 无匹配: []

        Example:
            >>> result = await manager.search_eventID_by_name_async("连壁")
            >>> print(result)
            [("3863", "《连壁》")]

            >>> result = await manager.search_eventID_by_name_async("哈")
            >>> print(result)
            [("3864", "《哈姆雷特》"), ("3865", "《哈利波特》")]
        """
        pass

    async def get_event_id_by_name(
        self,
        eName: str,
        default: str = "未找到该剧目",
        extra_id: Optional[int] = None
    ) -> MultiEventParseResult:
        """
        统一处理event_name转event_id逻辑

        Args:
            eName: 事件名称，例如: "连壁", "丽兹"
            default: 未找到时的默认错误消息
            extra_id: 当找到多个匹配时，指定选择第几个 (1-based index)

        Returns:
            MultiEventParseResult: 根据匹配情况返回不同格式

            情况1 - 找到唯一匹配:
                (EventID, None) 例如: ("3863", None)

            情况2 - 找到多个匹配且未指定extra_id:
                ([EventID, EventID, ...], 错误消息)
                例如: (["3863", "3864"], "找到多个匹配的剧名，请重新以唯一的关键词查询：\\n1. 《连壁》\\n2. 《哈姆雷特》")

            情况3 - 找到多个匹配且指定了valid extra_id:
                (EventID, None) 例如: ("3864", None)

            情况4 - 未找到匹配:
                (None, 错误消息) 例如: (None, "未找到该剧目")

        Example:
            >>> # 唯一匹配
            >>> result = await manager.get_event_id_by_name("连壁")
            >>> print(result)
            ("3863", None)

            >>> # 多个匹配
            >>> result = await manager.get_event_id_by_name("哈")
            >>> print(result)
            (["3864", "3865"], "找到多个匹配的剧名，请重新以唯一的关键词查询：\\n1. 《哈姆雷特》\\n2. 《哈利波特》")

            >>> # 指定选择第2个
            >>> result = await manager.get_event_id_by_name("哈", extra_id=2)
            >>> print(result)
            ("3865", None)
        """
        pass

    def verify_ticket_ids(self, ticket_ids: Union[str, List[TicketId]]) -> TicketVerificationResult:
        """
        验证票务ID列表的有效性

        Args:
            ticket_ids: 单个票务ID或票务ID列表
                       例如: "31777" 或 ["31777", "31778", "invalid123"]

        Returns:
            TicketVerificationResult: (有效ID列表, 无效ID列表)

            格式: ([有效TicketID, ...], [无效TicketID, ...])

        Example:
            >>> result = manager.verify_ticket_ids(["31777", "31778", "invalid123"])
            >>> print(result)
            (["31777", "31778"], ["invalid123"])

            >>> result = manager.verify_ticket_ids("31777")
            >>> print(result)
            (["31777"], [])
        """
        pass

    async def compare_to_database_async(self) -> CompareResultDict:
        """
        异步比较数据库变化，返回票务更新信息

        Returns:
            CompareResultDict: 完整的比较结果字典

            结构说明:
            {
                "events": {
                    EventID: [TicketID, TicketID, ...],  # 有更新的事件及其票务
                    "3863": ["31777", "31778"],
                    "3864": ["31779"]
                },
                "events_prefixes": {
                    EventID: "格式化的事件前缀信息",  # 用于推送消息的前缀
                    "3863": "剧名: 《连壁》\\n购票链接: https://clubz.cloudsation.com/event/3863.html\\n更新时间: 2025-07-10 15:30:00"
                },
                "categorized": {
                    "new": [TicketID, ...],      # 新上架的票务ID
                    "add": [TicketID, ...],      # 补票的票务ID
                    "pending": [TicketID, ...],  # 待开票的票务ID
                    "return": [TicketID, ...],   # 回流票的票务ID
                    "sold": [TicketID, ...],     # 售罄的票务ID
                    "back": [TicketID, ...]      # 增票的票务ID
                },
                "tickets": {
                    TicketID: {
                        "message": "格式化的票务消息",
                        "categorized": "更新状态",
                        "event_id": EventID
                    },
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

        Example:
            >>> result = await manager.compare_to_database_async()
            >>> print("新上架票务:", result["categorized"]["new"])
            >>> print("补票:", result["categorized"]["add"])
        """
        pass

    def get_events(self) -> Dict[EventId, EventInfoDict]:
        """
        获取所有事件数据

        Returns:
            Dict[EventId, EventInfoDict]: EventID -> 事件信息字典

            格式示例:
            {
                "3863": {
                    "id": "3863",
                    "title": "《连壁》",
                    "location": "上海",
                    "start_time": "2025-07-19 00:00:00",
                    "end_time": "2025-08-15 23:59:59",
                    "update_time": "2025-07-10 15:30:00",
                    "ticket_details": {
                        "31777": TicketDetailDict,
                        "31778": TicketDetailDict
                    }
                },
                "3864": { ... }
            }

        Example:
            >>> events = manager.get_events()
            >>> print("事件数量:", len(events))
            >>> print("第一个事件:", list(events.keys())[0])
        """
        pass

    def get_ticket(
        self,
        ticket_id: TicketId,
        event_id: Optional[EventId] = None,
        default: Any = None
    ) -> Optional[TicketDetailDict]:
        """
        获取单个票务详细信息

        Args:
            ticket_id: 票务ID，例如: "31777"
            event_id: 事件ID（可选），例如: "3863"
            default: 未找到时返回的默认值

        Returns:
            Optional[TicketDetailDict]: 票务详细信息字典或默认值

            成功返回格式示例:
            {
                "id": "31777",
                "event_id": "3863",
                "title": "《连壁》07-19 19:30￥199（原价￥299) 学生票",
                "start_time": "2025-07-19 19:30:00",
                "end_time": "2025-07-19 21:00:00",
                "status": "active",
                "ticket_price": 199,
                "total_ticket": 14,
                "left_ticket_count": 2,
                "cast": [{"artist": "韩冰儿", "role": "连壁"}],
                "city": "上海"
            }

        Example:
            >>> ticket = manager.get_ticket("31777")
            >>> if ticket:
            >>>     print(f"票务标题: {ticket['title']}")
            >>>     print(f"余票: {ticket['left_ticket_count']}/{ticket['total_ticket']}")
        """
        pass

    async def generate_tickets_query_message(
        self,
        event_id: EventId,
        show_cast: bool = True,
        ignore_sold_out: bool = False,
        refresh: bool = False,
        show_ticket_id: bool = False
    ) -> str:
        """
        生成票务查询消息

        Args:
            event_id: 事件ID，例如: "3863"
            show_cast: 是否显示卡司信息
            ignore_sold_out: 是否忽略已售罄场次
            refresh: 是否强制刷新数据
            show_ticket_id: 是否显示票务ID

        Returns:
            str: 格式化的票务查询消息

            消息格式示例:
            '''
            剧名: 《连壁》
            购票链接：https://clubz.cloudsation.com/event/3863.html
            最后更新时间：2025-07-10 15:30:00
            剩余票务信息:
            ✨《连壁》07-19 19:30￥199（原价￥299) 学生票 余票2/14 韩冰儿 胥子含
            ❌《连壁》07-20 14:30￥199（原价￥299) 学生票 余票0/10 韩冰儿 胥子含
            🕰️《连壁》07-21 19:30￥199（原价￥299) 学生票 余票5/20 即将开票，开票时间：2025-07-21 18:00:00

            数据更新时间: 2025-07-10 15:30:00
            '''

        Example:
            >>> message = await manager.generate_tickets_query_message("3863", show_cast=True)
            >>> print(message)
        """
        pass


class AnnotatedAliasManager:
    """
    别名管理器 - 详细注解版本
    """

    def get_alias_data(self) -> AliasDataDict:
        """
        获取完整的别名系统数据

        Returns:
            AliasDataDict: 别名数据字典

            完整结构示例:
            {
                "alias_to_event": {
                    "丽兹": "3863",           # 用户别名 -> EventID
                    "连璧": "3863",
                    "哈姆": "3864"
                },
                "event_to_names": {
                    "3863": ["连壁", "Lizzie", "丽兹"],    # EventID -> 所有搜索名称
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

        Example:
            >>> alias_data = manager.get_alias_data()
            >>> print("别名数量:", len(alias_data["alias_to_event"]))
            >>> print("事件数量:", len(alias_data["event_to_names"]))
        """
        pass

    def get_ordered_search_names(
        self,
        title: Optional[str] = None,
        event_id: Optional[EventId] = None
    ) -> List[SearchName]:
        """
        根据优先级获取有序的搜索名称列表

        Args:
            title: 标题或别名，例如: "丽兹", "连壁"
            event_id: 事件ID，例如: "3863"

        Returns:
            List[SearchName]: 有序的搜索名称列表

            优先级规则:
            1. 如果event_id存在，返回该事件的所有搜索名称
            2. 如果title是已知别名，返回对应事件的搜索名称
            3. 如果title是搜索名称，返回该事件的所有搜索名称
            4. 否则返回[title]作为搜索名称

        Example:
            >>> # 使用事件ID
            >>> names = manager.get_ordered_search_names(event_id="3863")
            >>> print(names)
            ["连壁", "Lizzie", "丽兹"]

            >>> # 使用别名
            >>> names = manager.get_ordered_search_names(title="丽兹")
            >>> print(names)
            ["连壁", "Lizzie", "丽兹"]

            >>> # 使用未知名称
            >>> names = manager.get_ordered_search_names(title="新剧名")
            >>> print(names)
            ["新剧名"]
        """
        pass


class AnnotatedStatsDataManager:
    """
    统计数据管理器 - 详细注解版本
    """

    def get_user_repos(self, user_id: UserId) -> List[str]:
        """
        获取用户的所有repo记录（格式化字符串）

        Args:
            user_id: 用户ID，例如: "1234567890"

        Returns:
            List[str]: 格式化的repo记录列表

            每个字符串格式示例:
            "ID: 1001 | 剧目: 《连壁》 | 日期: 2025-07-19 | 座位: A区1排1座 | 实付: 199 | 原价: 299 | 类型: 学生票 | 描述: 视野很好"

        Example:
            >>> repos = manager.get_user_repos("1234567890")
            >>> for repo in repos:
            >>>     print(repo)
        """
        pass

    def get_event_repos(
        self,
        event_id: EventId,
        price_filter: Optional[str] = None
    ) -> List[str]:
        """
        获取特定事件的repo记录

        Args:
            event_id: 事件ID，例如: "3863"
            price_filter: 价格过滤器（可选），例如: "199"

        Returns:
            List[str]: 格式化的repo记录列表

            过滤规则:
            - 如果price_filter为None，返回所有该事件的记录
            - 如果指定price_filter，只返回匹配价格的记录

        Example:
            >>> # 获取所有记录
            >>> repos = manager.get_event_repos("3863")
            >>> print(f"《连壁》共有 {len(repos)} 条记录")

            >>> # 筛选199元的记录
            >>> repos_199 = manager.get_event_repos("3863", "199")
            >>> print(f"199元价位共有 {len(repos_199)} 条记录")
        """
        pass

    def get_latest_repos(self, count: int = 10) -> List[str]:
        """
        获取最新的repo记录

        Args:
            count: 返回数量，最大不超过MAX_LATEST_REPOS_COUNT (20)

        Returns:
            List[str]: 按时间倒序的格式化记录列表

            返回最新的count条记录，按创建时间倒序排列

        Example:
            >>> latest = manager.get_latest_repos(5)
            >>> print("最新5条记录:")
            >>> for i, repo in enumerate(latest, 1):
            >>>     print(f"{i}. {repo}")
        """
        pass


class AnnotatedSaojuDataManager:
    """
    扫剧数据管理器 - 详细注解版本
    """

    async def get_data_by_date_async(
        self,
        date: str,
        update_delta_max_hours: int = 1
    ) -> Optional[List[SaojuShowDict]]:
        """
        获取指定日期的演出数据（支持缓存）

        Args:
            date: 日期字符串，格式: "YYYY-MM-DD"，例如: "2025-07-19"
            update_delta_max_hours: 缓存有效时间（小时），默认1小时

        Returns:
            Optional[List[SaojuShowDict]]: 演出数据列表或None

            成功返回的列表中每个字典格式:
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

        Example:
            >>> shows = await manager.get_data_by_date_async("2025-07-19")
            >>> if shows:
            >>>     print(f"2025-07-19 共有 {len(shows)} 场演出")
            >>>     for show in shows:
            >>>         print(f"{show['time']} {show['musical']} @ {show['city']}")
        """
        pass

    async def search_for_musical_by_date_async(
        self,
        search_name: Union[str, List[str]],
        date_time: str,
        city: Optional[str] = None
    ) -> Optional[SaojuShowDict]:
        """
        按日期时间搜索特定音乐剧

        Args:
            search_name: 搜索名称，可以是:
                        - 字符串: "连壁"
                        - 字符串列表: ["连", "壁"] (所有关键词都要包含)
            date_time: 日期时间，格式: "YYYY-MM-DD HH:MM"，例如: "2025-07-19 19:30"
            city: 城市过滤器（可选），例如: "上海"

        Returns:
            Optional[SaojuShowDict]: 匹配的演出信息或None

            匹配规则:
            1. 剧名匹配：search_name 必须包含在 musical 字段中
            2. 时间精确匹配：时间部分必须完全相等
            3. 城市匹配（如果指定）：city 必须包含在演出城市中

        Example:
            >>> # 字符串搜索
            >>> show = await manager.search_for_musical_by_date_async(
            ...     "连壁", "2025-07-19 19:30", "上海"
            ... )
            >>> if show:
            >>>     print(f"找到演出: {show['musical']} @ {show['venue']}")

            >>> # 多关键词搜索
            >>> show = await manager.search_for_musical_by_date_async(
            ...     ["连", "壁"], "2025-07-19 19:30"
            ... )
        """
        pass

    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict[str, Any]: 缓存统计信息字典

            结构示例:
            {
                "cached_dates_count": 5,                    # 已缓存的日期数量
                "total_shows_cached": 23,                   # 总共缓存的演出数量
                "oldest_cache": "2025-07-15 10:00:00",     # 最早缓存时间
                "newest_cache": "2025-07-19 15:30:00"      # 最新缓存时间
            }

        Example:
            >>> cache_info = manager.get_cache_info()
            >>> print(f"已缓存 {cache_info['cached_dates_count']} 个日期")
            >>> print(f"总共 {cache_info['total_shows_cached']} 场演出")
        """
        pass

    async def batch_update_dates(self, dates: List[str]) -> Dict[str, bool]:
        """
        批量更新多个日期的数据

        Args:
            dates: 日期列表，例如: ["2025-07-19", "2025-07-20", "2025-07-21"]

        Returns:
            Dict[str, bool]: 更新结果字典，日期 -> 是否成功

            结果示例:
            {
                "2025-07-19": True,   # 更新成功
                "2025-07-20": True,   # 更新成功
                "2025-07-21": False   # 更新失败
            }

        Example:
            >>> dates = ["2025-07-19", "2025-07-20", "2025-07-21"]
            >>> results = await manager.batch_update_dates(dates)
            >>>
            >>> success_count = sum(results.values())
            >>> print(f"成功更新 {success_count}/{len(dates)} 个日期")
            >>>
            >>> for date, success in results.items():
            >>>     status = "✅" if success else "❌"
            >>>     print(f"{status} {date}")
        """
        pass


# 使用示例和最佳实践

def detailed_annotation_examples():
    """
    详细注解的使用示例和最佳实践
    """

    print("=== 详细类型注解的好处 ===")
    benefits = [
        "1. 明确的数据结构：开发者清楚知道每个字段的含义和格式",
        "2. 减少调试时间：通过注解快速理解数据流向和转换",
        "3. 更好的IDE支持：自动完成和错误检查更准确",
        "4. 文档即代码：注解本身就是最好的文档",
        "5. 团队协作：新成员能快速理解代码结构",
        "6. 重构安全：类型检查帮助发现潜在问题"
    ]

    for benefit in benefits:
        print(benefit)

    print("\n=== 最佳实践 ===")
    practices = [
        "1. 函数注解要包含具体的数据格式示例",
        "2. 复杂结构使用单独的类型定义文件",
        "3. 返回值注解要说明不同情况下的返回格式",
        "4. 字典和列表要明确内容结构",
        "5. 可选参数要说明默认行为",
        "6. 异常情况要在注解中说明"
    ]

    for practice in practices:
        print(practice)


if __name__ == "__main__":
    detailed_annotation_examples()