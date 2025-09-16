"""
基础接口定义
定义数据管理模块的通用接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from .data_types import *


class DataManagerProtocol(ABC):
    """数据管理器协议接口"""

    @abstractmethod
    async def save(self, on_close: bool = False) -> Dict[str, Any]:
        """保存数据到持久化存储"""
        pass

    @abstractmethod
    def load(self) -> None:
        """从持久化存储加载数据"""
        pass

    @abstractmethod
    def on_load(self, *args, **kwargs) -> None:
        """数据加载后的初始化操作"""
        pass


class EventManagerProtocol(ABC):
    """事件管理器协议接口"""

    @abstractmethod
    async def get_event_by_id(self, event_id: EventId) -> Optional[EventInfo]:
        """根据事件ID获取事件信息"""
        pass

    @abstractmethod
    async def search_events_by_name(self, name: str) -> SearchResults:
        """根据名称搜索事件"""
        pass

    @abstractmethod
    async def get_tickets_by_event(self, event_id: EventId) -> TicketsDict:
        """获取事件的所有票务信息"""
        pass


class TicketManagerProtocol(ABC):
    """票务管理器协议接口"""

    @abstractmethod
    def get_ticket_by_id(self, ticket_id: TicketId, event_id: Optional[EventId] = None) -> Optional[TicketInfo]:
        """根据票务ID获取票务信息"""
        pass

    @abstractmethod
    def verify_ticket_ids(self, ticket_ids: List[TicketId]) -> Tuple[List[TicketId], List[TicketId]]:
        """验证票务ID列表，返回(有效ID列表, 无效ID列表)"""
        pass


class AliasManagerProtocol(ABC):
    """别名管理器协议接口"""

    @abstractmethod
    def add_alias(self, event_id: EventId, alias: Alias) -> bool:
        """添加别名"""
        pass

    @abstractmethod
    def get_event_id_by_alias(self, alias: Alias) -> Optional[EventId]:
        """通过别名获取事件ID"""
        pass

    @abstractmethod
    def get_search_names(self, event_id: EventId) -> List[SearchName]:
        """获取事件的所有搜索名称"""
        pass


class StatsManagerProtocol(ABC):
    """统计管理器协议接口"""

    @abstractmethod
    def record_command_usage(self, command: str) -> None:
        """记录命令使用次数"""
        pass

    @abstractmethod
    def create_repo_record(self, **kwargs) -> str:
        """创建repo记录，返回记录ID"""
        pass

    @abstractmethod
    def get_user_repos(self, user_id: UserId) -> List[RepoRecord]:
        """获取用户的所有repo记录"""
        pass


class ComparisonEngineProtocol(ABC):
    """数据比较引擎协议接口"""

    @abstractmethod
    def compare_ticket_data(self, old_data: Any, new_data: Any) -> Dict[str, List[TicketInfo]]:
        """比较票务数据变化"""
        pass

    @abstractmethod
    async def generate_comparison_result(self, comparison_data: ComparisonData) -> CompareResult:
        """生成比较结果"""
        pass