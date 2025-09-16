"""
数据管理模块重构总结和使用指南

本文档提供了重构后模块的使用方法和最佳实践
"""

from typing import Dict, List, Optional, Any, Tuple
from .core_models.data_types import *
from .core_models.protocols import *

# 重构后的模块导入示例
from .AliasManager_refactored import AliasManager
from .StatsDataManager_refactored import StatsDataManager
from .SaojuDataManager_refactored import SaojuDataManager


class DataManagerFactory:
    """数据管理器工厂类，统一管理所有数据管理器实例"""

    _instances = {}

    @classmethod
    def get_alias_manager(cls) -> AliasManager:
        """获取别名管理器单例"""
        if 'alias' not in cls._instances:
            cls._instances['alias'] = AliasManager()
        return cls._instances['alias']

    @classmethod
    def get_stats_manager(cls) -> StatsDataManager:
        """获取统计管理器单例"""
        if 'stats' not in cls._instances:
            cls._instances['stats'] = StatsDataManager()
        return cls._instances['stats']

    @classmethod
    def get_saoju_manager(cls) -> SaojuDataManager:
        """获取扫剧管理器单例"""
        if 'saoju' not in cls._instances:
            cls._instances['saoju'] = SaojuDataManager()
        return cls._instances['saoju']


# 使用示例

def example_alias_management():
    """别名管理使用示例"""
    alias_manager = DataManagerFactory.get_alias_manager()

    # 添加别名
    event_id = "12345"
    alias_manager.add_alias(event_id, "丽兹")
    alias_manager.add_search_name(event_id, "Lizzie")

    # 查询别名
    eid = alias_manager.get_event_id_by_alias("丽兹")
    search_names = alias_manager.get_search_names(event_id)

    # 获取有序搜索名称
    ordered_names = alias_manager.get_ordered_search_names(title="丽兹")

    print(f"Event ID: {eid}")
    print(f"Search names: {search_names}")
    print(f"Ordered names: {ordered_names}")


async def example_stats_management():
    """统计管理使用示例"""
    stats_manager = DataManagerFactory.get_stats_manager()

    # 记录命令使用
    stats_manager.record_command_usage("hlq_search")

    # 创建repo记录
    repo_id = stats_manager.create_repo_record(
        title="哈姆雷特",
        date="2025-08-15",
        price="199",
        seat="A区1排1座",
        content="视野很好",
        user_id="user123",
        category="学生票",
        payable="299"
    )

    # 获取用户记录
    user_repos = stats_manager.get_user_repos("user123")

    print(f"Created repo ID: {repo_id}")
    print(f"User repos: {user_repos}")


async def example_saoju_management():
    """扫剧管理使用示例"""
    saoju_manager = DataManagerFactory.get_saoju_manager()

    # 获取日期演出数据
    shows = await saoju_manager.get_data_by_date_async("2025-08-15")

    # 搜索特定演出
    show = await saoju_manager.search_for_musical_by_date_async(
        search_name="哈姆雷特",
        date_time="2025-08-15 19:30",
        city="上海"
    )

    # 获取缓存信息
    cache_info = saoju_manager.get_cache_info()

    print(f"Shows count: {len(shows) if shows else 0}")
    print(f"Found show: {show}")
    print(f"Cache info: {cache_info}")


# HulaquanDataManager 重构指南

class HulaquanDataManagerRefactored:
    """
    呼啦圈数据管理器重构指南

    由于原模块过于复杂，这里提供重构建议和核心方法的类型注解示例
    """

    def __init__(self, file_path: Optional[str] = None) -> None:
        """初始化管理器"""
        pass

    # 核心数据访问方法
    def get_events(self) -> EventsDict:
        """获取所有事件数据"""
        return self.data.get("events", {})

    def get_event(self, event_id: EventId, default: Any = None) -> Optional[EventInfo]:
        """获取单个事件信息"""
        return self.get_events().get(str(event_id), default)

    def get_ticket(self, ticket_id: TicketId, event_id: Optional[EventId] = None, default: Any = None) -> Optional[TicketInfo]:
        """获取票务信息"""
        if not event_id:
            event_id = self.ticket_id_to_event_id(ticket_id)

        if event_id and event_id in self.get_events():
            tickets = self.get_events()[event_id].get("ticket_details", {})
            return tickets.get(ticket_id, default)
        return default

    def verify_ticket_ids(self, ticket_ids: List[TicketId]) -> Tuple[List[TicketId], List[TicketId]]:
        """验证票务ID列表"""
        if isinstance(ticket_ids, str):
            ticket_ids = [ticket_ids]

        valid_ids = []
        invalid_ids = []

        for tid in ticket_ids:
            if self.ticket_id_to_event_id(tid, raise_error=False):
                valid_ids.append(tid)
            else:
                invalid_ids.append(tid)

        return valid_ids, invalid_ids

    # 异步方法类型注解
    async def search_events_by_name_async(self, event_name: str) -> List[Tuple[EventId, str]]:
        """异步搜索事件"""
        pass

    async def update_events_data_async(self) -> Dict[str, Any]:
        """异步更新事件数据"""
        pass

    async def generate_tickets_query_message(
        self,
        event_id: EventId,
        show_cast: bool = True,
        ignore_sold_out: bool = False,
        refresh: bool = False,
        show_ticket_id: bool = False
    ) -> str:
        """生成票务查询消息"""
        pass

    async def compare_to_database_async(self) -> CompareResult:
        """比较数据库变化"""
        pass


# 重构建议和最佳实践

class RefactoringGuidelines:
    """
    重构指导原则和建议
    """

    PRINCIPLES = [
        "1. 类型安全：所有公共方法都应有明确的类型注解",
        "2. 单一职责：每个方法只负责一个明确的功能",
        "3. 接口分离：使用协议接口定义模块间的契约",
        "4. 依赖注入：通过工厂模式管理依赖关系",
        "5. 错误处理：使用类型安全的Optional和Union类型",
        "6. 文档完整：每个方法都应有清晰的docstring",
        "7. 测试友好：方法设计应便于单元测试"
    ]

    DATA_STRUCTURE_IMPROVEMENTS = [
        "1. 使用dataclass定义数据结构，提供类型安全和自动生成方法",
        "2. 使用Enum定义常量，避免魔法字符串",
        "3. 统一命名规范，提高代码可读性",
        "4. 分离数据模型和业务逻辑",
        "5. 提供数据验证和转换方法"
    ]

    PERFORMANCE_OPTIMIZATIONS = [
        "1. 异步方法使用类型注解，明确返回类型",
        "2. 批量操作使用生成器和异步迭代器",
        "3. 缓存策略使用类型安全的包装器",
        "4. 数据库操作使用连接池和事务管理",
        "5. 内存管理使用弱引用和及时清理"
    ]


# 迁移指南

def migration_checklist():
    """
    迁移检查清单

    从旧模块迁移到重构模块时的步骤：
    """
    steps = [
        "1. 备份现有数据文件",
        "2. 安装新的类型注解依赖（typing_extensions如需要）",
        "3. 更新导入语句使用重构后的模块",
        "4. 运行类型检查工具（mypy, pyright）验证类型正确性",
        "5. 执行单元测试确保功能完整性",
        "6. 监控生产环境性能指标",
        "7. 逐步替换旧接口调用"
    ]

    return steps


if __name__ == "__main__":
    # 运行示例
    print("=== 别名管理示例 ===")
    example_alias_management()

    print("\n=== 重构指导原则 ===")
    for principle in RefactoringGuidelines.PRINCIPLES:
        print(principle)

    print("\n=== 迁移检查清单 ===")
    for step in migration_checklist():
        print(step)