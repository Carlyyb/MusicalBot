"""
重构后的 StatsDataManager
添加了完整的类型注解和改进的方法结构
"""

from typing import Dict, List, Optional, Any, Union
from plugins.AdminPlugin.BaseDataManager import BaseDataManager
from .core_models.data_types import EventId, UserId, RepoRecord
from .core_models.protocols import StatsManagerProtocol
from .utils import now_time_str
import copy


# 常量定义
ON_COMMAND_TIMES = "on_command_times"
HLQ_TICKETS_REPO = "hlq_tickets_repo"
USER_ID = 'user_id'
REPORT_ID = 'report_id'
LATEST_REPO_ID = 'latest_repo_id'
REPORT_ERROR_DETAILS = 'report_error_details'
EVENT_ID_TO_EVENT_TITLE = 'event_id_to_event_title'
LATEST_EVENT_ID = 'latest_event_id'
LATEST_20_REPOS = 'latest_20_repos'

MAX_LATEST_REPOS_COUNT = 20
MAX_ERROR_TIMES = 3


class StatsDataManager(BaseDataManager, StatsManagerProtocol):
    """
    统计数据管理器

    功能：
    - 记录命令使用统计
    - 管理学生票座位记录
    - 处理用户报告和错误反馈
    - 维护事件标题映射
    """

    def __init__(self, file_path: Optional[str] = None) -> None:
        super().__init__(file_path)

    def on_load(self) -> None:
        """初始化数据结构"""
        self.data.setdefault(ON_COMMAND_TIMES, {})
        self.data.setdefault(HLQ_TICKETS_REPO, {})
        self.data.setdefault(EVENT_ID_TO_EVENT_TITLE, {})
        self.data.setdefault(LATEST_REPO_ID, 1000)
        self.data.setdefault(LATEST_EVENT_ID, 100000)
        self.data.setdefault(LATEST_20_REPOS, [])  # [(event_id, report_id)]
        self.check_events_to_title_dict()

    def record_command_usage(self, command_name: str) -> None:
        """
        记录命令使用次数

        Args:
            command_name: 命令名称
        """
        self.data[ON_COMMAND_TIMES].setdefault(command_name, 0)
        self.data[ON_COMMAND_TIMES][command_name] += 1

    def get_command_usage_count(self, command_name: str) -> int:
        """
        获取命令使用次数

        Args:
            command_name: 命令名称

        Returns:
            使用次数
        """
        return self.data[ON_COMMAND_TIMES].get(command_name, 0)

    def generate_new_id(self, id_key: str) -> str:
        """
        生成新的ID

        Args:
            id_key: ID键名

        Returns:
            新生成的ID
        """
        self.data[id_key] += 1
        return str(self.data[id_key])

    def create_repo_record(
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
        创建学生票座位记录

        Args:
            title: 剧目标题
            date: 日期
            price: 实付价格
            seat: 座位信息
            content: 描述内容
            user_id: 用户ID
            category: 类别
            payable: 原价
            img: 图片URL（可选）
            event_id: 事件ID（可选）

        Returns:
            记录ID
        """
        price = str(price)
        user_id = str(user_id)
        event_id = self.register_event(title, event_id)

        if event_id not in self.data[HLQ_TICKETS_REPO]:
            self.data[HLQ_TICKETS_REPO][event_id] = {}

        report_id = self.generate_new_id(LATEST_REPO_ID)
        self.data[HLQ_TICKETS_REPO][event_id][report_id] = {
            USER_ID: user_id,
            "content": content,
            "price": price,
            "seat": seat,
            "img": img,
            "date": date,
            "category": category,
            "payable": payable,
            "create_time": now_time_str(),
            "event_title": title,
            "event_id": event_id,
            REPORT_ID: report_id,
            REPORT_ERROR_DETAILS: {},
        }

        self.add_to_latest_repos(report_id, event_id)
        return report_id

    def delete_repo_record(self, report_id: str, user_id: UserId) -> Optional[List[str]]:
        """
        删除repo记录

        Args:
            report_id: 记录ID
            user_id: 用户ID

        Returns:
            删除的记录信息列表，如果删除失败则返回None
        """
        user_id = str(user_id)
        for event_id, repos in self.data[HLQ_TICKETS_REPO].items():
            if report_id in repos:
                repo = repos[report_id]
                if repo[USER_ID] == user_id:
                    del repos[report_id]
                    self.remove_from_latest_repos(report_id, event_id)
                    return [self.format_repo_display(repo)]
        return None

    def get_user_repos(self, user_id: UserId) -> List[str]:
        """
        获取用户的所有repo记录

        Args:
            user_id: 用户ID

        Returns:
            格式化的记录列表
        """
        user_id = str(user_id)
        user_repos = []

        for event_id, repos in self.data[HLQ_TICKETS_REPO].items():
            for report_id, repo in repos.items():
                if repo[USER_ID] == user_id:
                    user_repos.append(self.format_repo_display(repo))

        return user_repos

    def get_event_repos(self, event_id: EventId, price_filter: Optional[str] = None) -> List[str]:
        """
        获取特定事件的repo记录

        Args:
            event_id: 事件ID
            price_filter: 价格过滤器（可选）

        Returns:
            格式化的记录列表
        """
        event_id = str(event_id)
        if event_id not in self.data[HLQ_TICKETS_REPO]:
            return []

        repos = []
        for report_id, repo in self.data[HLQ_TICKETS_REPO][event_id].items():
            if price_filter is None or repo["price"] == price_filter:
                repos.append(self.format_repo_display(repo))

        return repos

    def modify_repo_record(
        self,
        user_id: UserId,
        report_id: str,
        date: Optional[str] = None,
        seat: Optional[str] = None,
        price: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        payable: Optional[str] = None,
        is_op: bool = False
    ) -> Optional[List[str]]:
        """
        修改repo记录

        Args:
            user_id: 用户ID
            report_id: 记录ID
            date: 新日期（可选）
            seat: 新座位（可选）
            price: 新价格（可选）
            content: 新内容（可选）
            category: 新类别（可选）
            payable: 新原价（可选）
            is_op: 是否为管理员操作

        Returns:
            修改后的记录信息，如果失败则返回None
        """
        user_id = str(user_id)

        for event_id, repos in self.data[HLQ_TICKETS_REPO].items():
            if report_id in repos:
                repo = repos[report_id]
                if repo[USER_ID] == user_id or is_op:
                    # 更新字段
                    if date is not None:
                        repo["date"] = date
                    if seat is not None:
                        repo["seat"] = seat
                    if price is not None:
                        repo["price"] = str(price)
                    if content is not None:
                        repo["content"] = content
                    if category is not None:
                        repo["category"] = category
                    if payable is not None:
                        repo["payable"] = payable

                    return [self.format_repo_display(repo)]
        return None

    def report_repo_error(self, report_id: str, user_id: UserId, error_content: str = "") -> str:
        """
        报告repo错误

        Args:
            report_id: 记录ID
            user_id: 报告用户ID
            error_content: 错误内容

        Returns:
            处理结果消息
        """
        user_id = str(user_id)

        for event_id, repos in self.data[HLQ_TICKETS_REPO].items():
            if report_id in repos:
                repo = repos[report_id]
                error_details = repo.setdefault(REPORT_ERROR_DETAILS, {})
                error_details.setdefault("count", 0)
                error_details["count"] += 1
                error_details.setdefault("reporters", [])

                if user_id not in error_details["reporters"]:
                    error_details["reporters"].append(user_id)

                if error_content:
                    error_details.setdefault("details", [])
                    error_details["details"].append({
                        "user": user_id,
                        "content": error_content,
                        "time": now_time_str()
                    })

                # 如果错误次数过多，删除记录
                if error_details["count"] >= MAX_ERROR_TIMES:
                    del repos[report_id]
                    self.remove_from_latest_repos(report_id, event_id)
                    return f"记录 {report_id} 因错误反馈过多已被删除"

                return f"已记录对 {report_id} 的错误反馈"

        return f"未找到记录 {report_id}"

    def register_event(self, title: str, event_id: Optional[EventId] = None) -> EventId:
        """
        注册事件并分配ID

        Args:
            title: 事件标题
            event_id: 指定的事件ID（可选）

        Returns:
            事件ID
        """
        if event_id:
            event_id = str(event_id)
            self.data[EVENT_ID_TO_EVENT_TITLE][event_id] = title
            return event_id

        # 查找是否已存在该标题的事件
        for eid, existing_title in self.data[EVENT_ID_TO_EVENT_TITLE].items():
            if existing_title == title:
                return eid

        # 创建新事件ID
        new_event_id = self.generate_new_id(LATEST_EVENT_ID)
        self.data[EVENT_ID_TO_EVENT_TITLE][new_event_id] = title
        return new_event_id

    def get_event_title(self, event_id: EventId) -> Optional[str]:
        """
        获取事件标题

        Args:
            event_id: 事件ID

        Returns:
            事件标题或None
        """
        return self.data[EVENT_ID_TO_EVENT_TITLE].get(str(event_id))

    def get_event_id(self, title: str) -> Optional[EventId]:
        """
        通过标题获取事件ID

        Args:
            title: 事件标题

        Returns:
            事件ID或None
        """
        for event_id, existing_title in self.data[EVENT_ID_TO_EVENT_TITLE].items():
            if existing_title == title:
                return event_id
        return None

    def get_latest_repos(self, count: int = 10) -> List[str]:
        """
        获取最新的repo记录

        Args:
            count: 返回数量

        Returns:
            格式化的记录列表
        """
        count = min(count, MAX_LATEST_REPOS_COUNT)
        latest_records = []

        for event_id, report_id in reversed(self.data[LATEST_20_REPOS][-count:]):
            if event_id in self.data[HLQ_TICKETS_REPO] and report_id in self.data[HLQ_TICKETS_REPO][event_id]:
                repo = self.data[HLQ_TICKETS_REPO][event_id][report_id]
                latest_records.append(self.format_repo_display(repo))

        return latest_records

    def add_to_latest_repos(self, report_id: str, event_id: EventId) -> None:
        """
        添加到最新记录列表

        Args:
            report_id: 记录ID
            event_id: 事件ID
        """
        latest_repos = self.data[LATEST_20_REPOS]
        latest_repos.append((str(event_id), report_id))

        # 保持列表长度不超过限制
        if len(latest_repos) > MAX_LATEST_REPOS_COUNT:
            latest_repos.pop(0)

    def remove_from_latest_repos(self, report_id: str, event_id: EventId) -> None:
        """
        从最新记录列表中移除

        Args:
            report_id: 记录ID
            event_id: 事件ID
        """
        latest_repos = self.data[LATEST_20_REPOS]
        item = (str(event_id), report_id)
        if item in latest_repos:
            latest_repos.remove(item)

    def format_repo_display(self, repo: Dict[str, Any]) -> str:
        """
        格式化repo记录用于显示

        Args:
            repo: repo记录

        Returns:
            格式化字符串
        """
        return (
            f"ID: {repo[REPORT_ID]} | "
            f"剧目: {repo['event_title']} | "
            f"日期: {repo['date']} | "
            f"座位: {repo['seat']} | "
            f"实付: {repo['price']} | "
            f"原价: {repo['payable']} | "
            f"类型: {repo['category']} | "
            f"描述: {repo['content']}"
        )

    def check_events_to_title_dict(self) -> None:
        """检查和更新事件标题字典的一致性"""
        # 这里可以添加数据一致性检查逻辑
        pass