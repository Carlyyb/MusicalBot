"""
重构后的 AliasManager
添加了完整的类型注解和改进的方法结构
"""

from typing import Dict, List, Optional, Tuple, Any
from plugins.AdminPlugin.BaseDataManager import BaseDataManager
from .core_models.data_types import EventId, Alias, SearchName, AliasData
from .core_models.protocols import AliasManagerProtocol


class AliasManager(BaseDataManager, AliasManagerProtocol):
    """
    别名系统管理器

    功能：
    - 管理剧目别名到事件ID的映射
    - 管理事件ID到搜索名称的映射
    - 跟踪无响应查询次数
    - 支持数据迁移
    """

    def __init__(self, file_path: Optional[str] = "data/data_manager/alias.json", *args, **kwargs) -> None:
        super().__init__(file_path, *args, **kwargs)

    def on_load(self, *args, **kwargs) -> None:
        """初始化数据结构并处理旧数据迁移"""
        # 数据结构说明：
        # alias_to_event: {alias -> event_id}  # alias为用户设置的别名，不能直接用于外部系统检索
        # event_to_names: {event_id -> [search_name, ...]}  # search_name为可在外部系统检索到event的正式名称或关键词
        # name_to_alias: {search_name -> event_id}  # search_name可直接检索event
        # no_response: {alias:search_name -> int}  # 记录alias+search_name组合的无响应次数

        # 旧数据自动迁移
        if self.data and not self.data.get("alias_to_event") and any(
            isinstance(v, dict) and "search_names" in v for v in self.data.values()
        ):
            self.migrate_old_data(self.data)

        if not self.data or not self.data.get("alias_to_event"):
            self.data = {
                "alias_to_event": {},
                "event_to_names": {},
                "name_to_alias": {},
                "no_response": {}
            }

    def get_alias_data(self) -> AliasData:
        """获取结构化的别名数据"""
        return AliasData(
            alias_to_event=self.data.get("alias_to_event", {}),
            event_to_names=self.data.get("event_to_names", {}),
            name_to_alias=self.data.get("name_to_alias", {}),
            no_response=self.data.get("no_response", {})
        )

    def add_alias(self, event_id: EventId, alias: Alias) -> bool:
        """
        添加别名（alias），alias为用户设置的别名，不能直接用于外部系统检索

        Args:
            event_id: 事件ID
            alias: 用户设置的别名

        Returns:
            操作是否成功
        """
        event_id = str(event_id)
        alias = alias.strip().lower()
        self.data["alias_to_event"][alias] = event_id
        return True

    def add_search_name(self, event_id: EventId, search_name: SearchName) -> bool:
        """
        添加可检索名（search_name），search_name为可在外部系统检索到event的正式名称或关键词

        Args:
            event_id: 事件ID
            search_name: 搜索名称

        Returns:
            操作是否成功
        """
        event_id = str(event_id)
        search_name = search_name.strip()

        self.data["event_to_names"].setdefault(event_id, [])
        if search_name not in self.data["event_to_names"][event_id]:
            self.data["event_to_names"][event_id].append(search_name)

        self.data["name_to_alias"][search_name] = event_id
        return True

    def delete_alias(self, alias: Alias) -> bool:
        """
        删除别名

        Args:
            alias: 要删除的别名

        Returns:
            是否成功删除
        """
        alias = alias.strip().lower()
        event_id = self.data["alias_to_event"].pop(alias, None)

        if event_id:
            # 删除相关的 no_response 记录
            keys_to_delete = [k for k in self.data["no_response"].keys() if k.startswith(f"{alias}:")]
            for key in keys_to_delete:
                del self.data["no_response"][key]
            return True
        return False

    def delete_search_name(self, event_id: EventId, search_name: SearchName) -> bool:
        """
        删除搜索名称

        Args:
            event_id: 事件ID
            search_name: 要删除的搜索名称

        Returns:
            操作是否成功
        """
        event_id = str(event_id)
        search_name = search_name.strip()

        if event_id in self.data["event_to_names"]:
            self.data["event_to_names"][event_id] = [
                n for n in self.data["event_to_names"][event_id] if n != search_name
            ]
            if not self.data["event_to_names"][event_id]:
                del self.data["event_to_names"][event_id]

        self.data["name_to_alias"].pop(search_name, None)
        return True

    def set_no_response(self, alias: Alias, search_name: SearchName, reset: bool = False) -> None:
        """
        设置或更新无响应次数

        Args:
            alias: 别名
            search_name: 搜索名称
            reset: 是否重置计数
        """
        key = f"{alias}:{search_name}"
        if reset:
            self.data["no_response"][key] = 0
        else:
            self.data["no_response"][key] = self.data["no_response"].get(key, 0) + 1
            if self.data["no_response"][key] >= 2:
                self.delete_alias(alias)

    def get_search_names(self, event_id: EventId) -> List[SearchName]:
        """
        获取事件的所有搜索名称

        Args:
            event_id: 事件ID

        Returns:
            搜索名称列表
        """
        event_id = str(event_id)
        return self.data["event_to_names"].get(event_id, [])

    def get_event_id_by_alias(self, alias: Alias) -> Optional[EventId]:
        """
        通过别名获取事件ID

        Args:
            alias: 别名

        Returns:
            事件ID或None
        """
        alias = alias.strip().lower()
        return self.data["alias_to_event"].get(alias)

    def get_event_id_by_name(self, search_name: SearchName) -> Optional[EventId]:
        """
        通过搜索名称获取事件ID

        Args:
            search_name: 搜索名称

        Returns:
            事件ID或None
        """
        return self.data["name_to_alias"].get(search_name.strip())

    def get_ordered_search_names(self, title: Optional[str] = None, event_id: Optional[EventId] = None) -> List[SearchName]:
        """
        根据event_id或title，结合别名系统，返回排序有意义的检索名（search_name）列表

        优先级：
        1. 若event_id存在且在别名系统中，返回别名系统中该event_id的所有search_name（按添加顺序）
        2. 若title存在且为别名（alias），查找其event_id并返回对应search_name列表
        3. 若title本身为search_name，直接返回[title]
        4. 否则返回空列表

        Args:
            title: 标题/别名
            event_id: 事件ID

        Returns:
            搜索名称列表
        """
        # 优先用event_id
        if event_id:
            event_id = str(event_id)
            search_names = self.data.get("event_to_names", {}).get(event_id)
            if search_names:
                return list(search_names)

        # 其次用title查alias
        if title:
            t = title.strip()
            # 1. 作为alias查event_id
            eid = self.get_event_id_by_alias(t)
            if eid:
                search_names = self.data.get("event_to_names", {}).get(eid)
                if search_names:
                    return list(search_names)

            # 2. 作为search_name查event_id
            eid2 = self.get_event_id_by_name(t)
            if eid2:
                search_names = self.data.get("event_to_names", {}).get(eid2)
                if search_names:
                    return list(search_names)

            # 3. title本身为search_name
            return [t]

        return []

    def migrate_old_data(self, old_data: Dict[str, Any]) -> None:
        """
        迁移旧别名数据结构到新结构

        旧结构：{alias: {alias, search_names, event_id, ...}}
        新结构：见类文档注释

        Args:
            old_data: 旧数据结构
        """
        new_data = {
            "alias_to_event": {},
            "event_to_names": {},
            "name_to_alias": {},
            "no_response": {}
        }

        for alias, info in old_data.items():
            if not isinstance(info, dict) or "event_id" not in info:
                continue

            event_id = str(info["event_id"])
            new_data["alias_to_event"][alias] = event_id
            new_data["event_to_names"].setdefault(event_id, [])

            if alias not in new_data["event_to_names"][event_id]:
                new_data["event_to_names"][event_id].append(alias)

            # 迁移search_names
            for search_name in info.get("search_names", {}):
                if search_name not in new_data["event_to_names"][event_id]:
                    new_data["event_to_names"][event_id].append(search_name)
                new_data["name_to_alias"][search_name] = event_id

                # 迁移无响应次数
                no_resp = info["search_names"][search_name].get("no_response_times", 0)
                if no_resp:
                    new_data["no_response"][f"{alias}:{search_name}"] = no_resp

            new_data["name_to_alias"][alias] = event_id

        self.data = new_data