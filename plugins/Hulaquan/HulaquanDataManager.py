from datetime import datetime, timedelta
import unicodedata
from plugins.Hulaquan.SaojuDataManager import SaojuDataManager
import requests
import re
import aiohttp
import os, shutil
import copy
import asyncio
import json
import random
from plugins.AdminPlugin.BaseDataManager import BaseDataManager

"""
    更新思路：
    1.按照是否修改self将函数数据分类
    """



class HulaquanDataManager(BaseDataManager):
    """
    功能：
    1.存储/调取卡司排期数据
    2.根据卡司数据有效期刷新
    
    {
        "events":{}
        "update_time":datetime
    }
    """
    def __init__(self, file_path=None):
        #file_path = file_path or "data/Hulaquan/hulaquan_events_data.json"
        super().__init__(file_path)
        self.data["pending_events_dict"] = self.data.get("pending_events_dict", {}) # 确保有一个pending_events_dict来存储待办事件
        
    def _check_data(self):
        self.data.setdefault("events", {})  # 确保有一个事件字典来存储数据

    async def get_events_dict_async(self):
        data = await self.search_all_events_async()
        data_dic = {"events": {}, "update_time": ""}
        keys_to_extract = ["id", "title", "location", "start_time", "end_time", "update_time", "deadline", "create_time"]
        for event in data:
            event_id = str(event["id"])
            if event_id not in data_dic["events"]:
                data_dic["events"][event_id] = {key: event.get(key, None) for key in keys_to_extract}
        data_dic["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return data_dic

    async def search_all_events_async(self):
        data = False
        cnt = 95
        while data is False:
            count, result = await self.search_events_data_by_recommendation_link_async(cnt, 0, True)
            data = result
            cnt -= 5
            if cnt != 90 and not data:
                print(f"获取呼啦圈数据失败，第{(19-cnt/5)}尝试。")
            if cnt == 0:
                raise Exception
        return data

    async def search_events_data_by_recommendation_link_async(self, limit=12, page=0, timeMark=True, tags=None):
        recommendation_url = "https://clubz.cloudsation.com/site/getevent.html?filter=recommendation&access_token="
        try:
            recommendation_url = recommendation_url + "&limit=" + str(limit) + "&page=" + str(page)
            async with aiohttp.ClientSession() as session:
                async with session.get(recommendation_url, timeout=8) as response:
                    json_data = await response.text()
                    json_data = json_data.encode().decode("utf-8-sig")  # 关键：去除BOM
                    json_data = json.loads(json_data)
                    if isinstance(json_data, bool):
                        return False, False
                    result = []
                    for event in json_data["events"]:
                        if not timeMark or (timeMark and event["timeMark"] > 0):
                            if not tags or (tags and any(tag in event["tags"] for tag in tags)):
                                result.append(event["basic_info"])
                    return json_data["count"], result
        except Exception as e:
            return f"Error fetching recommendation: {e}", False


    
    async def _update_events_data_async(self, data_dict=None, __dump=True):
        data_dict = data_dict or await self.get_events_dict_async()
        self.updating = True
        self.data["events"] = data_dict["events"]
        event_ids = list(self.data["events"].keys())
        # 并发批量更新
        await asyncio.gather(*(self._update_ticket_details_async(eid) for eid in event_ids))
        self.data["last_update_time"] = self.data.get("update_time", None)
        self.data["update_time"] = data_dict["update_time"]
        self.updating = False
        return self.data

    async def _update_ticket_details_async(self, event_id, data_dict=None):
            json_data = await self.search_event_by_id_async(event_id)
            keys_to_extract = ["id","event_id","title", "start_time", "end_time","status","create_time","ticket_price","total_ticket", "left_ticket_count", "left_days", "valid_from"]
            ticket_list = json_data["ticket_details"]
            for i in range(len(ticket_list)):
                ticket_list[i] = {key: ticket_list[i].get(key, None) for key in keys_to_extract}
                if ticket_list[i]["total_ticket"] is None and ticket_list[i]["left_ticket_count"] is None:
                    del ticket_list[i]
            if data_dict is None:
                self.data["events"][event_id]["ticket_details"] = ticket_list
                return self.data
            else:
                data_dict["events"][event_id]["ticket_details"] = ticket_list
                return data_dict

    
    async def return_events_data(self):
        if not self.data.get("events", None):
            await self._update_events_data_async()
            print("呼啦圈数据已更新")
        return self.data["events"]

    async def search_eventID_by_name(self, event_name):
        data = await self.return_events_data()
        result = []
        for eid, event in data.items():
            title = event["title"]
            if re.search(event_name, title, re.IGNORECASE):
                result.append([eid, title])
        return result
    
    async def search_event_by_id_async(self, event_id):
        event_url = f"https://clubz.cloudsation.com/event/getEventDetails.html?id={event_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(event_url, timeout=8) as resp:
                json_data = await resp.text()
                json_data = json_data.encode().decode("utf-8-sig")  # 关键：去除BOM
                return json.loads(json_data)
        
    async def output_data_info(self):
        old_data = await self.return_events_data()
        for eid, event in old_data.items():
            print(eid, event["title"], event["end_time"], event["update_time"])
        
    # ------------------------------------------ #


    def get_max_ticket_content_length(self, tickets):
        max_len = 0
        for ticket in tickets:
            s = f"{ticket['title']} 余票{ticket['left_ticket_count']}/{ticket['total_ticket']}"
            max_len = max(max_len, get_display_width(s))
        return max_len

    # -------------------Query------------------------------ #         
    # ---------------------Announcement--------------------- #
    async def compare_to_database_async(self, __dump=True):
        if __dump:
            old_data_all = copy.deepcopy(self.data)
            new_data_all = await self._update_events_data_async()
        else:
            old_data_all = self.data
            new_data_all = await self._update_events_data_async()
        return self.__compare_to_database(old_data_all, new_data_all)
        
    def __compare_to_database(self, old_data_all, new_data_all):
        # 将新爬的数据与旧数据进行比较，找出需要更新的数据
        """
        __dump: bool, 是否将新数据写入文件
        Returns:
            update_data: list, 包含需要更新的事件数据
            None: 如果没有需要更新的数据
        """
        is_updated = False
        new_pending = False
        new_data = new_data_all.get("events", {})
        old_data = old_data_all.get("events", {})
        messages = []
        for eid, event in new_data.items(): # 一个id对应一部剧
            message = []
            if comp := self.compare_tickets(old_data.get(eid, {}), new_data[eid].get("ticket_details", None)):
                # 仅返回更新了的ticket detail
                new_message = []
                return_message = []
                add_message = []
                pending_message = {}
                for ticket in comp:
                    flag = ticket.get('update_status')
                    t = ("✨" if ticket['left_ticket_count'] > 0 else "❌") + f"{ticket['title']} 余票{ticket['left_ticket_count']}/{ticket['total_ticket']}"
                    if ticket["status"] == "pending" and 'update_status' in ticket.keys():
                        valid_from = ticket["valid_from"]
                        if not valid_from or valid_from == "null":
                            valid_from = "未公开"
                        pending_message[valid_from] = []
                        pending_message[valid_from].append(t)
                    elif ticket["status"] == "active":
                        if flag == 'new':
                            new_message.append(t)
                        elif flag == 'return':
                            return_message.append(t)
                        elif flag == 'add':
                            add_message.append(t)
                if pending_message:
                    new_pending = True
                    t = "🟡新上架场次：\n"
                    cnt = 1
                    for valid_from, m in pending_message.items():
                        s = (f"第{cnt}波" if len(pending_message.keys()) > 1 else None)+f"开票时间：{valid_from}\n"+'\n'.join(m)+"\n"
                        cnt += 1
                        random_id = random.randint(1000, 9999)
                        valid_date = standardize_datetime(valid_from, return_str=False)
                        while random_id in pending_message:
                            random_id = random.randint(1000, 9999)
                        self.data["pending_events_dict"][random_id] = {
                            "valid_from": valid_date,
                            "message": (f"剧名: {event['title']}\n"
                                        f"活动结束时间: {event['end_time']}\n"
                                        f"更新时间: {self.data['update_time']}\n"
                                        f"开票时间: {valid_from}\n"
                                        f"场次信息：\n" + '\n'.join(m) + "\n"
                                        )
                                        
                        }
                        t += s
                    message.append(t)
                if new_message:
                    message.append("🟢新开票场次：\n"+'\n'.join(new_message))
                if add_message:
                    message.append("🟢补票场次：\n"+'\n'.join(add_message))
                if return_message:
                    message.append("🟢回流（？）场次：\n"+'\n'.join(return_message))
            else:
                continue
            messages.append((
                f"剧名: {event['title']}\n"
                f"活动结束时间: {event['end_time']}\n"
                f"更新时间: {self.data['update_time']}\n"
            ) + "\n".join(message))
            is_updated = True
            if is_updated:
                cache_root = os.path.join(os.getcwd(), "update_data_cache")
                os.makedirs(cache_root, exist_ok=True)
                # 清理超过48小时的缓存
                now = datetime.now()
                for d in os.listdir(cache_root):
                    dir_path = os.path.join(cache_root, d)
                    if os.path.isdir(dir_path):
                        try:
                            # 目录名格式为"2025-07-03_12-34-56"
                            dir_time = datetime.strptime(d, "%Y-%m-%d_%H-%M-%S")
                            if now - dir_time > timedelta(hours=48):
                                shutil.rmtree(dir_path)
                        except Exception:
                            continue
                # 新建本次缓存
                update_time_str = str(self.data['update_time']).replace(":", "-").replace(" ", "_")
                cache_dir = os.path.join(cache_root, update_time_str)
                os.makedirs(cache_dir, exist_ok=True)
                with open(os.path.join(cache_dir, "old_data_all.json"), "w", encoding="utf-8") as f:
                    json.dump(old_data_all, f, ensure_ascii=False, indent=2)
                with open(os.path.join(cache_dir, "new_data_all.json"), "w", encoding="utf-8") as f:
                    json.dump(new_data_all, f, ensure_ascii=False, indent=2)
        return {"is_updated": is_updated, "messages": messages, "new_pending": new_pending}

    

    def compare_tickets(self, old_data_all, new_data):
        """
{
  "id": 31777,
  "event_id": 3863,
  "title": "《海雾》07-19 20:00￥199（原价￥299) 学生票",
  "start_time": "2025-07-19 20:00:00",
  "end_time": "2025-07-19 21:00:00",
  "status": "active", /expired, /pending
  "create_time": "2025-06-11 11:06:13",
  "ticket_price": 199,
  "max_ticket": 1,
  "total_ticket": 14,
  "left_ticket_count": 0,
  "left_days": 25,
}
        """
        if (not old_data_all) and new_data:
            for i in new_data:
                i["update_status"] = 'new'
                
            return new_data
        elif not (old_data_all and new_data):
            return None
        else:
            old_data = old_data_all.get("ticket_details", {})
        if not old_data:
            for i in new_data:
                i["update_status"] = 'new'
            return new_data
        old_data_dict = {item['id']: item for item in old_data}
        update_data = []
        # 遍历 new_data 并根据条件进行更新
        for new_item in new_data:
            new_id = new_item['id']
            new_left_ticket_count = new_item['left_ticket_count']
            new_total_ticket = new_item['total_ticket']
            if new_id not in old_data_dict:
                # 如果 new_data 中存在新的 id，则标记为 "new"
                new_item['update_status'] = 'new'
                update_data.append(new_item)
            else:
                # 获取 old_data 中对应 id 的旧数据
                old_item = old_data_dict[new_id]
                old_left_ticket_count = old_item['left_ticket_count']
                old_total_ticket = old_item['total_ticket']
                #print("new_item", new_item, "\nold item", old_item)
                if new_total_ticket > old_total_ticket:
                    # 如果 total_ticket 增加了，则标记为 "add"
                    new_item['update_status'] = 'add'
                    update_data.append(new_item)
                elif new_left_ticket_count > old_left_ticket_count and old_left_ticket_count == 0:
                    # 如果 left_ticket_count 增加了，则标记为 "return"
                    new_item['update_status'] = 'return'
                    update_data.append(new_item)
                else:
                    new_item['update_status'] = None
        return update_data
        
        
    async def on_message_tickets_query(self, eName, saoju, ignore_sold_out=False, show_cast=True, refresh=False):
        query_time = datetime.now()
        result = await self.search_eventID_by_name(eName)
        if len(result) > 1:
            queue = [f"{i}. {event[1]}" for i, event in enumerate(result, start=1)]
            return f"找到多个匹配的剧名，请重新以唯一的关键词查询：\n" + "\n".join(queue)
        elif len(result) == 1:
            eid = result[0][0]
            return await self.generate_tickets_query_message(eid, query_time, eName, saoju, show_cast=show_cast, ignore_sold_out=ignore_sold_out)
        else:
            return "未找到该剧目。"

    async def generate_tickets_query_message(self, eid, query_time, eName, saoju:SaojuDataManager, show_cast=True, ignore_sold_out=False, refresh=False):
        if not refresh:
            event_data = self.data["events"].get(str(eid), None)
        else:
            await self._update_ticket_details_async(eid)
            event_data = self.data["events"].get(str(eid), None)
        if event_data:
            title = event_data.get("title", "未知剧名")
            tickets_details = event_data.get("ticket_details", [])
            remaining_tickets = []
            for ticket in tickets_details:
                if ticket["status"] == "active":
                    if ticket["left_ticket_count"] > (0 if ignore_sold_out else -1):
                        remaining_tickets.append(ticket)
            max_ticket_info_count = self.get_max_ticket_content_length(remaining_tickets)
            url = f"https://clubz.cloudsation.com/event/{eid}.html"
            message = (
                f"剧名: {title}\n"
                f"购票链接：{url}\n"
                "剩余票务信息:\n"
                + ("\n".join([("✨" if ticket['left_ticket_count'] > 0 else "❌") 
                                + ljust_for_chinese(f"{ticket['title']} 余票{ticket['left_ticket_count']}/{ticket['total_ticket']}", max_ticket_info_count)
                                + ((" " + (" ".join(saoju.search_casts_by_date_and_name(eName, 
                                                                                ticket['start_time'], 
                                                                                city=extract_city(event_data.get("location", ""))
                                                                                )
                                                )
                                        )
                                ) if show_cast else "")
                                for ticket in remaining_tickets
                                ])
                if remaining_tickets else "暂无余票。")
                                )
            message += f"\n数据更新时间: {self.data['update_time']}\n"
            return message
        else:
            return "未找到该剧目的详细信息。"
        
    async def message_update_data_async(self):
        query_time = datetime.now()
        query_time_str = query_time.strftime("%Y-%m-%d %H:%M:%S")
        result = await self.compare_to_database_async()
        is_updated = result["is_updated"]
        messages = result["messages"]
        new_pending = result["new_pending"]
        if not is_updated:
            return {"is_updated": False, "messages": [f"无更新数据。\n查询时间：{query_time_str}\n上次数据更新时间：{self.data['last_update_time']}",], "new_pending": False}
        messages = [f"检测到呼啦圈有{len(messages)}条数据更新\n查询时间：{query_time_str}"] + messages
        return {"is_updated": is_updated, "messages": messages, "new_pending": new_pending}    
    

    # ---------------------静态函数--------------------- #
def get_display_width(s):
    width = 0
    for char in s:
        # 判断字符是否是全宽字符（通常是中文等）
        if unicodedata.east_asian_width(char) in ['F', 'W']:  # 'F' = Fullwidth, 'W' = Wide
            width += 3  # 全宽字符占用2个位置
        else:
            width += 1  # 半宽字符占用1个位置
    return width

def ljust_for_chinese(s, width, fillchar=' '):
    current_width = get_display_width(s)
    if current_width >= width:
        return s
    fill_width = width - current_width
    result = s + fillchar * fill_width
    return result

def standardize_datetime(dateAndTime: str, return_str=True):
    # 当前年份
    current_year = datetime.now().year
    dateAndTime = dateAndTime.replace("：", ':')
    
    # 尝试不同的日期时间格式
    formats = [
        "%Y-%m-%d %H:%M",  # 2025-12-07 06:30
        "%m-%d %H:%M",     # 12-07 06:30
        "%m-%d %H:%M:%S",  # 12-07 06:30:21
        "%y-%m-%d %H:%M",  # 25-12-07 06:30
        "%y/%m/%d %H:%M"   # 25/12/07 06:30
    ]
    for fmt in formats:
        try:
            # 如果年份不在字符串中, 默认使用当前年份
            if fmt[0] == "%y" or fmt[0] == "%Y":
                if dateAndTime[:2].isdigit() and len(dateAndTime.split()[0]) == 7:  # "25/12/07"
                    dateAndTime = str(current_year) + "-" + dateAndTime
                dt = datetime.strptime(dateAndTime, fmt)
            else:
                dt = datetime.strptime(dateAndTime, fmt)
            if len(str(dt.second)) == 0:
                dt = dt.replace(second=0)
            if return_str:
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                return dt
        except ValueError:
            continue
    raise ValueError("无法解析该日期时间格式")
        

def extract_city(address):
    city_pattern_1 = r'([^\s]{2})市'
    city_pattern_2 = r'([^\s]{4,})区'
    city_pattern_3 = r'([^\s]+省)'
    match = re.search(city_pattern_1, address)
    if match:
        return match.group(1)
    match = re.search(city_pattern_2, address)
    if match:
        return None

    match = re.search(city_pattern_3, address)
    if match:
        return match.group(1)[:-1]
    return None