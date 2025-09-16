"""
实际应用的重要函数注解更新
对原有函数添加详细的内容结构注解
"""

from typing import Dict, List, Optional, Union, Any, Tuple, Literal
from .core_models.detailed_types import *


# 更新现有的重要函数，添加详细注解

class AnnotatedHulaquanDataManagerUpdates:
    """
    对现有 HulaquanDataManager 中重要函数的详细注解更新
    """

    async def on_message_tickets_query(
        self,
        eName: str,
        ignore_sold_out: bool = False,
        show_cast: bool = True,
        refresh: bool = False,
        show_ticket_id: bool = False,
        extra_id: Optional[int] = None
    ) -> str:
        """
        处理票务查询消息的核心函数

        Args:
            eName: 事件名称，例如: "连壁", "丽兹", "哈姆雷特"
            ignore_sold_out: 是否忽略已售罄场次
            show_cast: 是否显示卡司信息
            refresh: 是否强制刷新数据
            show_ticket_id: 是否显示票务ID（用于关注功能）
            extra_id: 当搜索到多个结果时，指定选择第几个 (1-based)

        Returns:
            str: 格式化的查询结果消息

            消息格式示例:
            ```
            剧名: 《连壁》
            购票链接：https://clubz.cloudsation.com/event/3863.html
            最后更新时间：2025-07-10 15:30:00
            剩余票务信息:
            ✨ 31777《连壁》07-19 19:30￥199（原价￥299) 学生票 余票2/14 韩冰儿 胥子含
            ❌ 31778《连壁》07-20 14:30￥199（原价￥299) 学生票 余票0/10 韩冰儿 胥子含

            ⚠️未在扫剧网站上找到此剧卡司
            数据更新时间: 2025-07-10 15:30:00
            ```

            特殊返回值:
            - "未找到该剧目。" - 当 eName 无匹配时
            - "找到多个匹配的剧名，请重新以唯一的关键词查询..." - 多个匹配且无 extra_id

        Example:
            >>> # 基本查询
            >>> result = await hlq.on_message_tickets_query("连壁")

            >>> # 带选项的查询
            >>> result = await hlq.on_message_tickets_query(
            ...     "连壁",
            ...     ignore_sold_out=True,  # 忽略售罄
            ...     show_cast=True,        # 显示卡司
            ...     show_ticket_id=True    # 显示票务ID
            ... )

            >>> # 多匹配时指定选择
            >>> result = await hlq.on_message_tickets_query("哈", extra_id=2)
        """
        pass

    def compare_tickets(
        self,
        old_data_all: Optional[EventInfoDict],
        new_data: Optional[Dict[TicketId, TicketDetailDict]]
    ) -> Dict[str, List[TicketDetailDict]]:
        """
        比较新旧票务数据，检测变化

        Args:
            old_data_all: 旧的事件数据，包含 "ticket_details" 字段
                         格式: {"ticket_details": {TicketID: TicketDetailDict, ...}, ...}
                         例如: {"ticket_details": {"31777": {...}, "31778": {...}}}

            new_data: 新的票务数据映射
                     格式: {TicketID: TicketDetailDict, ...}
                     例如: {"31777": {...}, "31778": {...}, "31779": {...}}

        Returns:
            Dict[str, List[TicketDetailDict]]: 按更新状态分类的票务变化

            返回结构:
            {
                "new": [TicketDetailDict, ...],      # 新上架票务
                "add": [TicketDetailDict, ...],      # 总票数增加的票务
                "return": [TicketDetailDict, ...],   # 回流票（从0余票变为有余票）
                "sold": [TicketDetailDict, ...],     # 余票减少的票务
                "back": [TicketDetailDict, ...],     # 余票增加的票务
                "pending": [TicketDetailDict, ...]   # 待开票状态的票务
            }

            判断逻辑:
            - "new": 新票务ID，或总票数从0变为正数
            - "add": total_ticket 增加
            - "return": left_ticket_count 从0变为正数
            - "sold": left_ticket_count 减少
            - "back": left_ticket_count 增加（但不是从0开始）
            - "pending": status 为 "pending"

        Example:
            >>> old_data = {
            ...     "ticket_details": {
            ...         "31777": {"left_ticket_count": 0, "total_ticket": 10, ...},
            ...         "31778": {"left_ticket_count": 5, "total_ticket": 15, ...}
            ...     }
            ... }
            >>> new_data = {
            ...     "31777": {"left_ticket_count": 2, "total_ticket": 10, ...},  # 回流票
            ...     "31778": {"left_ticket_count": 3, "total_ticket": 15, ...},  # 余票减少
            ...     "31779": {"left_ticket_count": 5, "total_ticket": 20, ...}   # 新票
            ... }
            >>> result = hlq.compare_tickets(old_data, new_data)
            >>> print("回流票:", len(result.get("return", [])))
            >>> print("售出票:", len(result.get("sold", [])))
            >>> print("新票:", len(result.get("new", [])))
        """
        pass

    async def build_single_ticket_info_str(
        self,
        ticket: TicketDetailDict,
        show_cast: bool,
        city: str = "上海",
        show_ticket_id: bool = False
    ) -> Tuple[str, bool, Tuple[bool, str]]:
        """
        构建单条票务信息的显示字符串

        Args:
            ticket: 票务详细信息字典
                   必需字段示例:
                   {
                       "id": "31777",
                       "title": "《连壁》07-19 19:30￥199（原价￥299) 学生票",
                       "left_ticket_count": 2,
                       "total_ticket": 14,
                       "status": "active",  # "active" | "pending" | "expired"
                       "valid_from": "2025-07-19 18:00:00"
                   }

            show_cast: 是否显示卡司信息
            city: 城市名称（用于卡司查询）
            show_ticket_id: 是否在前面显示票务ID

        Returns:
            Tuple[str, bool, Tuple[bool, str]]: (票务信息字符串, 是否缺少卡司数据, (是否为待开票, 开票时间))

            返回值解析:
            [0] str: 格式化的票务信息字符串
                - 有票: "✨《连壁》07-19 19:30￥199（原价￥299) 学生票 余票2/14 韩冰儿 胥子含"
                - 售罄: "❌《连壁》07-19 19:30￥199（原价￥299) 学生票 余票0/14 韩冰儿 胥子含"
                - 待开票: "🕰️《连壁》07-19 19:30￥199（原价￥299) 学生票 余票5/20"
                - 带ID: " 31777✨《连壁》07-19 19:30￥199（原价￥299) 学生票 余票2/14"

            [1] bool: 是否缺少卡司数据（当 show_cast=True 但查不到卡司时为 True）

            [2] Tuple[bool, str]: 待开票信息
                - (False, ""): 不是待开票状态
                - (True, "2025-07-19 18:00:00"): 待开票，开票时间
                - (True, "未知时间"): 待开票但时间未知

        Example:
            >>> ticket = {
            ...     "id": "31777",
            ...     "title": "《连壁》07-19 19:30￥199（原价￥299) 学生票",
            ...     "left_ticket_count": 2,
            ...     "total_ticket": 14,
            ...     "status": "active"
            ... }
            >>> info, no_cast, pending = await hlq.build_single_ticket_info_str(
            ...     ticket, show_cast=True, show_ticket_id=True
            ... )
            >>> print(info)
            # " 31777✨《连壁》07-19 19:30￥199（原价￥299) 学生票 余票2/14 韩冰儿 胥子含"
        """
        pass

    def get_ordered_search_names(
        self,
        title: Optional[str] = None,
        event_id: Optional[EventId] = None
    ) -> List[SearchName]:
        """
        获取按优先级排序的搜索名称列表（结合别名系统）

        Args:
            title: 用户输入的标题/别名，例如: "丽兹", "连壁", "Lizzie"
            event_id: 事件ID，例如: "3863"

        Returns:
            List[SearchName]: 按优先级排序的搜索名称列表

            优先级逻辑:
            1. 如果提供 event_id 且在别名系统中存在 → 返回该事件的所有搜索名称
            2. 如果 title 是已知别名 → 查找对应事件ID，返回该事件的搜索名称
            3. 如果 title 是已知搜索名称 → 返回对应事件的所有搜索名称
            4. 否则 → 返回 [title] 作为搜索尝试

            搜索名称排序: 按添加到别名系统的顺序排列

        Example:
            >>> # 情况1: 使用事件ID
            >>> names = hlq.get_ordered_search_names(event_id="3863")
            >>> print(names)
            ["连壁", "Lizzie", "丽兹"]  # 别名系统中该事件的所有搜索名称

            >>> # 情况2: 用户输入别名
            >>> names = hlq.get_ordered_search_names(title="丽兹")
            >>> print(names)
            ["连壁", "Lizzie", "丽兹"]  # "丽兹"是别名，返回对应事件的搜索名称

            >>> # 情况3: 用户输入搜索名称
            >>> names = hlq.get_ordered_search_names(title="连壁")
            >>> print(names)
            ["连壁", "Lizzie", "丽兹"]  # "连壁"是搜索名称，返回对应事件的所有名称

            >>> # 情况4: 未知名称
            >>> names = hlq.get_ordered_search_names(title="新剧名")
            >>> print(names)
            ["新剧名"]  # 直接使用输入作为搜索名称

        Notes:
            - 这个函数是搜索系统的核心，整合了别名系统的智能匹配
            - 返回的名称列表会被用于依次尝试API搜索
            - 空列表表示无法生成有效的搜索名称
        """
        pass


class AnnotatedAliasManagerUpdates:
    """
    对现有 AliasManager 中重要函数的详细注解更新
    """

    def add_alias(self, event_id: EventId, alias: Alias) -> bool:
        """
        添加用户别名到事件ID的映射

        Args:
            event_id: 事件ID，例如: "3863"
            alias: 用户设置的别名，例如: "丽兹", "连璧"
                  - 会被自动转换为小写: "丽兹" → "丽兹"
                  - 会被去除首尾空格

        Returns:
            bool: 添加是否成功 (目前总是返回 True)

        Side Effects:
            更新 self.data["alias_to_event"]:
            {
                "丽兹": "3863",      # 新增或更新
                "连璧": "3863",
                ...
            }

        Example:
            >>> # 添加别名
            >>> success = alias_mgr.add_alias("3863", "丽兹")
            >>> print(success)  # True

            >>> # 验证添加结果
            >>> event_id = alias_mgr.get_event_id_by_alias("丽兹")
            >>> print(event_id)  # "3863"

        Notes:
            - 别名是用户自定义的，不能直接用于外部系统API查询
            - 一个别名只能对应一个事件ID（会覆盖旧映射）
            - 一个事件ID可以有多个别名
        """
        pass

    def add_search_name(self, event_id: EventId, search_name: SearchName) -> bool:
        """
        添加可用于外部系统查询的搜索名称

        Args:
            event_id: 事件ID，例如: "3863"
            search_name: 搜索名称，例如: "连壁", "Lizzie"
                        - 这些名称可以直接用于API查询
                        - 会被去除首尾空格但保持原大小写

        Returns:
            bool: 添加是否成功 (目前总是返回 True)

        Side Effects:
            更新两个数据结构:
            1. self.data["event_to_names"]:
               {
                   "3863": ["连壁", "Lizzie", "丽兹"],  # 添加到列表（避免重复）
                   ...
               }
            2. self.data["name_to_alias"]:
               {
                   "连壁": "3863",     # 搜索名称 → 事件ID
                   "Lizzie": "3863",
                   ...
               }

        Example:
            >>> # 添加搜索名称
            >>> alias_mgr.add_search_name("3863", "连壁")
            >>> alias_mgr.add_search_name("3863", "Lizzie")

            >>> # 验证结果
            >>> search_names = alias_mgr.get_search_names("3863")
            >>> print(search_names)  # ["连壁", "Lizzie"]

            >>> event_id = alias_mgr.get_event_id_by_name("Lizzie")
            >>> print(event_id)  # "3863"

        Notes:
            - 搜索名称是经过验证可以在外部API中搜索到结果的名称
            - 同一搜索名称只能对应一个事件ID
            - 用于构建优先级搜索列表
        """
        pass

    def set_no_response(
        self,
        alias: Alias,
        search_name: SearchName,
        reset: bool = False
    ) -> None:
        """
        设置或更新别名+搜索名称组合的无响应次数

        Args:
            alias: 用户别名，例如: "丽兹"
            search_name: 搜索名称，例如: "Lizzie"
            reset: 是否重置计数
                  - True: 重置为0（找到了结果时）
                  - False: 计数+1（未找到结果时）

        Side Effects:
            更新 self.data["no_response"]:
            {
                "丽兹:Lizzie": 0,    # reset=True 时重置
                "丽兹:连壁": 1,      # reset=False 时递增
                "哈姆:Hamlet": 2,    # 达到阈值时会触发别名删除
                ...
            }

            当计数达到 2 次时，会自动删除该别名:
            - 调用 self.delete_alias(alias)
            - 清理相关的无响应记录

        Example:
            >>> # 搜索失败，增加计数
            >>> alias_mgr.set_no_response("丽兹", "Lizzie", reset=False)
            >>> alias_mgr.set_no_response("丽兹", "Lizzie", reset=False)
            >>> # 此时 "丽兹" 别名会被自动删除

            >>> # 搜索成功，重置计数
            >>> alias_mgr.set_no_response("连璧", "连壁", reset=True)

        Use Cases:
            - 在 HulaquanDataManager.get_event_id_by_name() 中调用
            - 搜索成功时 reset=True，失败时 reset=False
            - 自动清理无效的别名映射

        Notes:
            - 这是别名系统的自清理机制
            - 防止无效别名累积影响搜索性能
            - 阈值设为2次是为了避免偶发网络问题导致误删
        """
        pass


class AnnotatedStatsManagerUpdates:
    """
    对现有 StatsDataManager 中重要函数的详细注解更新
    """

    def new_repo(
        self,
        title: str,
        date: str,
        price: str,
        seat: str,
        content: str,
        user_id: UserId,
        category: str,
        payable: str,
        img: Optional[str] = None,
        event_id: Optional[EventId] = None
    ) -> str:
        """
        创建新的学生票座位记录

        Args:
            title: 剧目标题，例如: "连壁", "哈姆雷特"
            date: 观演日期，格式: "YYYY-MM-DD"，例如: "2025-07-19"
            price: 实际支付价格，例如: "199", "299"
            seat: 座位信息，例如: "A区1排1座", "VIP区第2排3号"
            content: 用户描述，例如: "视野很好", "音效清晰，推荐"
            user_id: 提交用户的ID，例如: "1234567890"
            category: 票务类别，例如: "学生票", "全价票", "其他"
            payable: 原价，例如: "299", "399"
            img: 图片URL（可选），例如: "https://example.com/seat.jpg"
            event_id: 指定事件ID（可选），例如: "3863"

        Returns:
            str: 生成的报告ID，例如: "1001", "1002"

        Side Effects:
            1. 注册或获取事件ID（如果未提供）
            2. 创建repo记录存储在 self.data[HLQ_TICKETS_REPO]:
               {
                   "3863": {
                       "1001": {
                           "user_id": "1234567890",
                           "content": "视野很好",
                           "price": "199",
                           "seat": "A区1排1座",
                           "img": "https://example.com/seat.jpg",
                           "date": "2025-07-19",
                           "category": "学生票",
                           "payable": "299",
                           "create_time": "2025-07-10 15:30:00",
                           "event_title": "连壁",
                           "event_id": "3863",
                           "report_id": "1001",
                           "report_error_details": {}
                       }
                   }
               }
            3. 添加到最新记录列表 self.data[LATEST_20_REPOS]
            4. 递增ID计数器 self.data[LATEST_REPO_ID]

        Example:
            >>> repo_id = stats_mgr.new_repo(
            ...     title="连壁",
            ...     date="2025-07-19",
            ...     price="199",
            ...     seat="A区1排1座",
            ...     content="视野很好，音效清晰",
            ...     user_id="1234567890",
            ...     category="学生票",
            ...     payable="299"
            ... )
            >>> print(f"创建的报告ID: {repo_id}")  # "1001"

        Notes:
            - 如果title已存在对应的event_id，会复用现有ID
            - 会自动生成create_time为当前时间
            - report_error_details 初始化为空字典，用于错误反馈
        """
        pass

    def modify_repo(
        self,
        user_id: UserId,
        repoID: str,
        date: Optional[str] = None,
        seat: Optional[str] = None,
        price: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        payable: Optional[str] = None,
        isOP: bool = False
    ) -> Optional[List[str]]:
        """
        修改用户的repo记录

        Args:
            user_id: 用户ID，例如: "1234567890"
            repoID: 要修改的报告ID，例如: "1001"
            date: 新的日期（可选），例如: "2025-07-20"
            seat: 新的座位信息（可选），例如: "B区2排5座"
            price: 新的价格（可选），例如: "249"
            content: 新的描述（可选），例如: "更新：视野极佳"
            category: 新的类别（可选），例如: "全价票"
            payable: 新的原价（可选），例如: "349"
            isOP: 是否为管理员操作（管理员可以修改任何记录）

        Returns:
            Optional[List[str]]: 修改成功时返回格式化的记录列表，失败时返回 None

            成功返回示例:
            [
                "ID: 1001 | 剧目: 连壁 | 日期: 2025-07-20 | 座位: B区2排5座 | 实付: 249 | 原价: 349 | 类型: 学生票 | 描述: 更新：视野极佳"
            ]

        Permission Logic:
            - 普通用户: 只能修改自己提交的记录 (record["user_id"] == user_id)
            - 管理员: 可以修改任何记录 (isOP == True)

        Example:
            >>> # 用户修改自己的记录
            >>> result = stats_mgr.modify_repo(
            ...     user_id="1234567890",
            ...     repoID="1001",
            ...     seat="B区2排5座",
            ...     price="249",
            ...     content="更新：视野更佳"
            ... )
            >>> if result:
            ...     print("修改成功:", result[0])
            ... else:
            ...     print("修改失败：记录不存在或无权限")

            >>> # 管理员修改任意记录
            >>> result = stats_mgr.modify_repo(
            ...     user_id="admin123",
            ...     repoID="1001",
            ...     content="管理员更新",
            ...     isOP=True
            ... )

        Notes:
            - 只有提供的字段会被更新，None值的字段保持不变
            - price会被自动转换为字符串类型
            - 修改后的记录保持原有的create_time和report_id不变
        """
        pass

    def get_event_student_seat_repo(
        self,
        event_id: EventId,
        event_price: Optional[str] = None
    ) -> List[str]:
        """
        获取指定事件的学生票座位记录

        Args:
            event_id: 事件ID，例如: "3863"
            event_price: 价格过滤器（可选），例如: "199"

        Returns:
            List[str]: 格式化的记录字符串列表

            返回格式（每条记录一个字符串）:
            "ID: 1001 | 剧目: 连壁 | 日期: 2025-07-19 | 座位: A区1排1座 | 实付: 199 | 原价: 299 | 类型: 学生票 | 描述: 视野很好"

            过滤逻辑:
            - 如果 event_price 为 None：返回该事件的所有记录
            - 如果指定 event_price：只返回价格匹配的记录

        Example:
            >>> # 获取所有连壁的记录
            >>> repos = stats_mgr.get_event_student_seat_repo("3863")
            >>> print(f"《连壁》共有 {len(repos)} 条座位记录")
            >>> for repo in repos:
            ...     print(repo)

            >>> # 只看199元价位的记录
            >>> repos_199 = stats_mgr.get_event_student_seat_repo("3863", "199")
            >>> print(f"199元价位有 {len(repos_199)} 条记录")

        Use Cases:
            - 用户查询特定剧目的座位反馈: /查询repo 连壁
            - 价格筛选: /查询repo 连壁 199
            - 为用户提供购票参考信息

        Notes:
            - 返回空列表表示该事件暂无记录
            - 记录按存储顺序返回（不保证特定排序）
            - 格式化字符串便于直接显示给用户
        """
        pass


# 实际使用的函数注解示例

def real_world_annotation_examples():
    """
    真实世界中如何使用这些详细注解的示例
    """

    print("=== 实际开发场景 ===")

    # 场景1: 新开发者理解数据流
    print("\n1. 新开发者理解数据流:")
    print("   通过注解快速了解函数的输入输出格式")
    print("   例如：看到 EventSearchResult 就知道返回 [[EventID, EventName], ...]")

    # 场景2: 调试数据结构
    print("\n2. 调试数据结构:")
    print("   当程序出错时，对照注解检查数据格式是否正确")
    print("   例如：compare_tickets 返回的字典结构和预期是否一致")

    # 场景3: API集成
    print("\n3. API集成:")
    print("   集成外部API时，清楚知道需要什么格式的数据")
    print("   例如：search_for_musical_by_date_async 需要的日期时间格式")

    # 场景4: 重构安全
    print("\n4. 重构安全:")
    print("   修改函数时，类型检查工具会根据注解提醒不兼容的改动")
    print("   例如：改变返回值格式时，调用方会收到类型警告")

    print("\n=== 注解质量标准 ===")
    standards = [
        "✅ 包含具体的数据结构示例",
        "✅ 说明不同情况下的返回格式",
        "✅ 提供实际的使用示例",
        "✅ 解释业务逻辑和边界情况",
        "✅ 标明副作用和状态变化",
        "✅ 包含错误处理说明"
    ]

    for standard in standards:
        print(standard)


if __name__ == "__main__":
    real_world_annotation_examples()