"""
重构后的 SaojuDataManager
添加了完整的类型注解和改进的方法结构
"""

from typing import Dict, List, Optional, Any, Union
import aiohttp
import asyncio
from datetime import datetime, timedelta
from plugins.AdminPlugin.BaseDataManager import BaseDataManager
from .core_models.data_types import SaojuEventInfo
from .utils import parse_datetime, dateTimeToStr, dateToStr, timeToStr


class SaojuDataManager(BaseDataManager):
    """
    扫剧网站数据管理器

    功能：
    - 获取扫剧网站的演出信息
    - 按日期缓存数据以提高性能
    - 支持过期数据自动刷新
    - 提供演出搜索和匹配功能
    """

    def __init__(self, file_path: Optional[str] = None) -> None:
        super().__init__(file_path)

    def on_load(self) -> None:
        """初始化数据结构"""
        self.data.setdefault("date_dict", {})  # 按日期存储演出数据
        self.data.setdefault("update_time_dict", {})  # 存储更新时间
        self.data["update_time_dict"].setdefault("date_dict", {})
        self.refresh_expired_data()

    async def search_day_async(self, date: str) -> Optional[Dict[str, Any]]:
        """
        异步搜索指定日期的演出数据

        Args:
            date: 日期字符串，格式为 YYYY-MM-DD

        Returns:
            演出数据字典，失败时返回None
        """
        url = "http://y.saoju.net/yyj/api/search_day/"
        data = {"date": date}
        max_retries = 5

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=data, timeout=10) as response:
                        response.raise_for_status()
                        json_response = await response.json()
                        return json_response

            except aiohttp.ClientError as http_err:
                print(f'SAOJU ERROR HTTP error occurred (attempt {attempt+1}): {http_err}')
            except Exception as err:
                print(f'SAOJU ERROR Other error occurred (attempt {attempt+1}): {err}')

            await asyncio.sleep(1)  # 每次失败后等待1秒再重试

        print('SAOJU ERROR: Failed to fetch data after 5 attempts.')
        return None

    async def get_data_by_date_async(
        self,
        date: str,
        update_delta_max_hours: int = 1
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取指定日期的演出数据，支持缓存

        Args:
            date: 日期字符串
            update_delta_max_hours: 缓存有效期（小时）

        Returns:
            演出数据列表，失败时返回None
        """
        # 检查缓存
        if date in self.data["date_dict"]:
            update_time = parse_datetime(self.data["update_time_dict"]["date_dict"].get(date))
            if update_time:
                if (datetime.now() - update_time) < timedelta(hours=update_delta_max_hours):
                    return self.data["date_dict"][date]

        # 获取新数据
        data = await self.search_day_async(date)
        if data:
            show_list = data.get("show_list", [])
            self.data["date_dict"][date] = show_list
            self.data["update_time_dict"]["date_dict"][date] = dateTimeToStr(datetime.now())
            return show_list

        return None

    async def search_for_musical_by_date_async(
        self,
        search_name: Union[str, List[str]],
        date_time: str,
        city: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        按日期和时间搜索特定音乐剧

        Args:
            search_name: 搜索名称，可以是字符串或字符串列表
            date_time: 日期时间字符串，格式为 %Y-%m-%d %H:%M
            city: 城市名称（可选）

        Returns:
            匹配的演出信息，未找到时返回None
        """
        # 解析日期时间
        date_time_obj = parse_datetime(date_time)
        _date = dateToStr(date_time_obj)
        _time = timeToStr(date_time_obj)

        # 获取当日演出数据
        data = await self.get_data_by_date_async(_date)
        if not data:
            return None

        # 搜索匹配的演出
        for show in data:
            musical = show.get("musical", "")
            show_time = show.get("time", "")
            show_city = show.get("city", "")

            # 检查城市匹配
            city_match = True
            if city:
                city_match = city in show_city

            # 检查时间匹配
            time_match = _time == show_time

            # 检查剧名匹配
            name_match = False
            if isinstance(search_name, str):
                name_match = search_name in musical
            elif isinstance(search_name, list):
                name_match = all(name in musical for name in search_name)

            if city_match and time_match and name_match:
                return self.convert_to_saoju_event_info(show)

        return None

    def convert_to_saoju_event_info(self, show_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将原始演出数据转换为结构化信息

        Args:
            show_data: 原始演出数据

        Returns:
            结构化的演出信息
        """
        return {
            "musical": show_data.get("musical", ""),
            "time": show_data.get("time", ""),
            "city": show_data.get("city", ""),
            "date": show_data.get("date", ""),
            "cast": show_data.get("cast", []),
            "venue": show_data.get("venue", ""),
            "price": show_data.get("price", ""),
            "url": show_data.get("url", "")
        }

    async def match_co_casts(
        self,
        cast_names: List[str],
        show_others: bool = True
    ) -> List[str]:
        """
        匹配共同演员的演出

        Args:
            cast_names: 演员名称列表
            show_others: 是否显示其他演员

        Returns:
            匹配结果消息列表
        """
        # 这里应该调用实际的演员匹配逻辑
        # 由于原代码中没有完整实现，这里提供接口框架
        messages = []

        # TODO: 实现演员匹配逻辑
        # 1. 搜索包含指定演员的所有演出
        # 2. 找出共同出演的其他演员
        # 3. 格式化输出信息

        return messages

    async def request_co_casts_data(
        self,
        cast_names: List[str],
        show_others: bool = True
    ) -> List[Dict[str, Any]]:
        """
        请求共同演员数据

        Args:
            cast_names: 演员名称列表
            show_others: 是否包含其他演员信息

        Returns:
            演员数据列表
        """
        # TODO: 实现演员数据请求逻辑
        return []

    def refresh_expired_data(self, max_age_hours: int = 24) -> None:
        """
        清理过期的缓存数据

        Args:
            max_age_hours: 数据最大保存时间（小时）
        """
        current_time = datetime.now()
        expired_dates = []

        for date, update_time_str in self.data["update_time_dict"]["date_dict"].items():
            update_time = parse_datetime(update_time_str)
            if update_time and (current_time - update_time) > timedelta(hours=max_age_hours):
                expired_dates.append(date)

        # 删除过期数据
        for date in expired_dates:
            self.data["date_dict"].pop(date, None)
            self.data["update_time_dict"]["date_dict"].pop(date, None)

    def get_cached_dates(self) -> List[str]:
        """
        获取所有已缓存的日期

        Returns:
            日期列表
        """
        return list(self.data["date_dict"].keys())

    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存信息字典
        """
        return {
            "cached_dates_count": len(self.data["date_dict"]),
            "total_shows_cached": sum(len(shows) for shows in self.data["date_dict"].values()),
            "oldest_cache": min(self.data["update_time_dict"]["date_dict"].values()) if self.data["update_time_dict"]["date_dict"] else None,
            "newest_cache": max(self.data["update_time_dict"]["date_dict"].values()) if self.data["update_time_dict"]["date_dict"] else None
        }

    async def batch_update_dates(self, dates: List[str]) -> Dict[str, bool]:
        """
        批量更新多个日期的数据

        Args:
            dates: 日期列表

        Returns:
            更新结果字典 {date: success}
        """
        results = {}

        # 创建并发任务
        tasks = [self.get_data_by_date_async(date, update_delta_max_hours=0) for date in dates]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for date, response in zip(dates, responses):
            if isinstance(response, Exception):
                results[date] = False
                print(f"Failed to update date {date}: {response}")
            else:
                results[date] = response is not None

        return results