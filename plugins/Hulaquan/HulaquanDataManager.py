from datetime import datetime, timedelta
from plugins.Hulaquan.utils import *
from plugins.Hulaquan import BaseDataManager
from .Exceptions import *
import aiohttp
import os, shutil
import copy
import json
import asyncio
import re

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
        super().__init__(file_path)
           
    def on_load(self):
        global Saoju, Stats, Alias
        import importlib
        
        dataManagers = importlib.import_module('plugins.Hulaquan.data_managers')
        Saoju = dataManagers.Saoju  # 动态获取
        Stats = dataManagers.Stats  # 动态获取
        Alias = dataManagers.Alias  # 动态获取
        self.semaphore = asyncio.Semaphore(10)  # 限制并发量10
        self.data.setdefault("events", {})  # 确保有一个事件字典来存储数据
        self.data["pending_events"] = self.data.get("pending_events", {}) # 确保有一个pending_events来存储待办事件
        self.data["ticket_id_to_event_id"] = self.data.get("ticket_id_to_event_id", {})
        self.update_ticket_dict_async()

    async def _update_events_dict_async(self):
        data = await self.search_all_events_async()
        data_dic = {"events": {}, "update_time": ""}
        keys_to_extract = ["id", "title", "location", "start_time", "end_time", "update_time", "deadline", "create_time"]
        for event in data:
            event_id = str(event["id"])
            Stats.register_event(event['title'], event_id)
            if event_id not in data_dic["events"]:
                data_dic["events"][event_id] = {key: event.get(key, None) for key in keys_to_extract}
        data_dic["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.data["events"] = data_dic["events"]
        self.data["last_update_time"] = self.data.get("update_time", None)
        self.data["update_time"] = data_dic["update_time"]
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
            if cnt == 75:
                raise RequestTimeoutException
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

    async def _update_events_data_async(self):
        if self.updating:
            return self.data
        self.updating = True
        try:
            await self._update_events_dict_async()
            event_ids = list(self.events().keys())
            # 并发批量更新
            await asyncio.gather(*(self._update_ticket_details_async(eid) for eid in event_ids))
        except RequestTimeoutException:
            self.updating = False
            raise
        except Exception as e:
            self.updating = False
            raise
        self.updating = False
        return self.data

    async def _update_ticket_details_async(self, event_id, data_dict=None):
        retry = 0
        while retry < 3:
            async with self.semaphore:
                try:
                    json_data = await self.search_event_by_id_async(event_id)
                    keys_to_extract = ["id","event_id","title", "start_time", "end_time","status","create_time","ticket_price","total_ticket", "left_ticket_count", "left_days", "valid_from"]
                    ticket_list = json_data["ticket_details"]
                    ticket_dump_list = {}
                    for i in range(len(ticket_list)):
                        ticket = ticket_list[i]
                        ticket['id'] = str(ticket['id'])
                        tid = ticket.get("id", None)
                        if not tid or ticket.get("total_ticket", None) is None or not ticket.get('start_time') or ticket.get("status") not in ['active', 'pending']:
                            if ticket.get("status") != "expired":
                                print(ticket)
                            continue
                        ticket_dump_list[tid] = {key: ticket.get(key, None) for key in keys_to_extract}
                        if tid not in self.data['ticket_id_to_event_id'].keys():
                            self.data['ticket_id_to_event_id'][tid] = event_id
                    if data_dict is None:
                        self.data["events"][event_id]["ticket_details"] = ticket_dump_list
                        return self.data
                    else:
                        data_dict["events"][event_id]["ticket_details"] = ticket_dump_list
                        return data_dict
                except asyncio.TimeoutError:
                    retry += 1
                    if retry >= 3:
                        print(f"event_id {event_id} 请求超时，已重试2次，跳过")
                        return {}
                    else:
                        print(f"event_id {event_id} 请求超时，重试第{retry}次……")
                        await asyncio.sleep(1)
                except Exception as e:
                    print(f"event_id {event_id} 请求异常：{e}")
                    raise
                    return {}

    
    def events(self):
        return self.data["events"]

    async def search_eventID_by_name_async(self, event_name):
        if self.updating:
            # 当数据正在更新时，等到数据全部更新完再继续
            await self._wait_for_data_update()
        data = self.events()
        result = []
        for eid, event in data.items():
            title = event["title"]
            if re.search(event_name, title, re.IGNORECASE):
                result.append([eid, title])
        return result
    
    async def search_event_by_id_async(self, event_id):
        event_url = f"https://clubz.cloudsation.com/event/getEventDetails.html?id={event_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(event_url, timeout=15) as resp:
                json_data = await resp.text()
                json_data = json_data.encode().decode("utf-8-sig")  # 关键：去除BOM
                return json.loads(json_data)
        
    async def output_data_info(self):
        old_data = self.events()
        for eid, event in old_data.items():
            print(eid, event["title"], event["end_time"], event["update_time"])
        
    # ------------------------------------------ #


    def get_max_ticket_content_length(self, tickets, ticket_title_key='title'):
        max_len = 0
        for ticket in tickets:
            s = f"{ticket[ticket_title_key]} 余票{ticket['left_ticket_count']}/{ticket['total_ticket']}"
            max_len = max(max_len, get_display_width(s))
        return max_len

    # -------------------Query------------------------------ #         
    # ---------------------Announcement--------------------- #
    async def compare_to_database_async(self, subscribe_list=[]):
        old_data_all = copy.deepcopy(self.data)
        new_data_all = await self._update_events_data_async()
        try:
            return await self.__compare_to_database(old_data_all, new_data_all, subscribe_list)
        except Exception as e:
            self.save_data_cache(old_data_all, new_data_all, "error_announcement_cache")
            raise  # 重新抛出异常，便于外层捕获和处理

    async def __compare_to_database(self, old_data_all, new_data_all, subscribe_list=[]):
        # 将新爬的数据与旧数据进行比较，找出需要更新的数据
        """
        __dump: bool, 是否将新数据写入文件
        Returns:
            update_data: list, 包含需要更新的事件数据
            None: 如果没有需要更新的数据
        """
        no_subscribe = subscribe_list is None
        if no_subscribe:
            subscribe_list = []
        is_updated = False
        new_pending = False
        new_data = new_data_all.get("events", {})
        old_data = old_data_all.get("events", {})
        messages = []
        for eid, event in new_data.items(): # 一个id对应一部剧
            message = []
            if comp := self.compare_tickets(old_data.get(eid, {}), new_data[eid].get("ticket_details", None), subscribe_list):
                # 仅返回更新了的ticket detail
                assemble = {}
                new_message = []
                return_message = []
                add_message = []
                subscribe_message = {i: [] for i in subscribe_list}
                pending_message = {}
                for ticket in comp:
                    flag = ticket.get('update_status')
                    tInfo = extract_title_info(ticket.get("title", ""))
                    event_title = tInfo['title'][1:-1]
                    t = ("✨" if ticket['left_ticket_count'] > 0 else "❌") + f"{ticket['title']} 余票{ticket['left_ticket_count']}/{ticket['total_ticket']}" + " " + await self.get_cast_artists_str_async(event_title, ticket)
                    if ticket["status"] == "pending":
                        valid_from = ticket.get("valid_from")
                        if not valid_from or valid_from == "null":
                            valid_from = "NG"
                        pending_message[valid_from] = []
                        pending_message[valid_from].append(t)
                    elif ticket["status"] == "active" and flag:
                        if flag == 'new':
                            if ticket["left_ticket_count"] == 0 and ticket['total_ticket'] == 0:
                                valid_from = ticket.get("valid_from")
                                if not valid_from or valid_from == "null":
                                    valid_from = "NG"
                                pending_message[valid_from] = []
                                pending_message[valid_from].append(t)
                            else:
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
                        s = (f"第{cnt}波" if len(pending_message.keys()) > 1 else "")+f"开票时间：{valid_from}\n"+'\n'.join(m)+"\n"
                        cnt += 1
                        
                        valid_date = standardize_datetime(valid_from, return_str=True) if valid_from != "NG" else "NG"
                        if valid_date in self.data["pending_events"]:
                            if eid in self.data["pending_events"][valid_date]:
                                self.data["pending_events"][valid_date][eid] += '\n'.join(m)
                            else:
                                self.data["pending_events"][valid_date][eid] = (
                                    f"剧名: {event['title']}\n"
                                            f"购票链接: https://clubz.cloudsation.com/event/{eid}.html\n"
                                            f"更新时间: {self.data['update_time']}\n"
                                            f"开票时间: {valid_from}\n"
                                            f"场次信息：\n" + '\n'.join(m) + "\n"
                                            )
                        else:
                            self.data["pending_events"][valid_date] = {
                                "valid_from": valid_date,
                                eid: (f"剧名: {event['title']}\n"
                                            f"购票链接: https://clubz.cloudsation.com/event/{eid}.html\n"
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
                    message.append("🟢回流场次：\n"+'\n'.join(return_message))
            else:
                continue
            url = f"https://clubz.cloudsation.com/event/{eid}.html"
            messages.append((
                f"剧名: {event['title']}\n"
                f"购票链接: {url}\n"
                f"更新时间: {self.data['update_time']}\n"
            ) + "\n".join(message))
            is_updated = True
            if is_updated:
                self.save_data_cache(old_data_all, new_data_all, "update_data_cache")
        return {"is_updated": is_updated, "messages": messages, "new_pending": new_pending}


    def save_data_cache(self, old_data_all, new_data_all, cache_folder_name):
        cache_root = os.path.join(os.getcwd(), cache_folder_name)
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


    def compare_tickets(self, old_data_all, new_data, subscribe_list):
        if (not old_data_all) and new_data:
            # 如果旧数据不存在，那么所有新数据都判定为新上架
            print("旧数据不存在，所有新数据都判定为新上架")
            for i in new_data:
                i["update_status"] = 'new'
            return list(new_data.values())
        elif not (old_data_all and new_data):
            # 如果旧数据新数据都为空 返回NONE
            return None
        else:
            old_data_dict = old_data_all.get("ticket_details", {})
        if not old_data_dict:
            # 如果旧数据没有票务细节项，所有新数据判定为新上架
            print("旧数据无票务细节，所有新数据都判定为新上架")
            for i in new_data.values():
                i["update_status"] = 'new'
            return list(new_data.values())
        
        # 以上情况都不存在，新旧数据都正常，则开始遍历
        
        update_data = []
        # 遍历 new_data 并根据条件进行更新
        for new_id in list(new_data.keys()):
            new_item = new_data[new_id]
            new_left_ticket_count = new_item['left_ticket_count']
            new_total_ticket = new_item['total_ticket']     
            if not new_item['title'] and not new_total_ticket:
                continue
            if new_id not in list(old_data_dict.keys()):
                # 如果 new_data 中存在新的 ticket id，则标记为 新上架
                new_item['update_status'] = 'new'
                update_data.append(new_item)
            else:
                # 如果 没有新的ticket id
                old_item = old_data_dict[new_id]
                old_left_ticket_count = old_item['left_ticket_count']
                old_total_ticket = old_item['total_ticket']
                is_subscribe = new_id in subscribe_list
                new_item['is_subscribe'] = is_subscribe # 如果ticketid在订阅列表中，则标记为被订阅
                
                if (new_total_ticket>0 and not old_total_ticket):
                    # 如果旧ticket的总票数为0或不存在，新的大于0，则为新开票
                    new_item['update_status'] = 'new'
                    update_data.append(new_item)
                elif (new_total_ticket > (old_total_ticket or 0)):
                    # 如果 total_ticket 增加了，则标记为 "add"
                    new_item['update_status'] = 'add'
                    update_data.append(new_item)
                elif old_left_ticket_count is None or (new_left_ticket_count > old_left_ticket_count and old_left_ticket_count == 0):
                    # 如果 left_ticket_count 增加了，则标记为 "return"
                    new_item['update_status'] = 'return'
                    update_data.append(new_item)
                elif is_subscribe and old_left_ticket_count > new_left_ticket_count:
                    new_item['update_status'] = 'sold'
                    update_data.append(new_item)
                elif is_subscribe and old_left_ticket_count < new_left_ticket_count:
                    new_item['update_status'] = 'return'
                    update_data.append(new_item)
                else:
                    new_item['update_status'] = None
        return update_data
    
    
    async def get_ticket_cast_and_city_async(self, eName, ticket, city=None):
        if not ticket['start_time']:
            return {"cast":[], "city":None}
        # 优先用别名系统检索名
        search_names = self.get_ordered_search_names(extract_text_in_brackets(eName, False), ticket['event_id'])
        for name in search_names:
            response = await Saoju.search_for_musical_by_date_async(name, ticket['start_time'], city=city)
            if response:
                Alias.set_no_response(eName, name, reset=True)
                cast = response.get("cast", [])
                ticket["cast"] = cast
                ticket['city'] = response.get('city', None)
                return {"cast": cast, "city": ticket.get('city', None)}
            else:
                Alias.set_no_response(eName, name, reset=False)
        return {"cast":[], "city":None}

    async def get_cast_artists_str_async(self, eName, ticket, city=None):
        cast = (await self.get_ticket_cast_and_city_async(eName, ticket, city))['cast']
        return " ".join([i["artist"] for i in cast])

    async def get_ticket_city_async(self, eName, ticket):
        return (await self.get_ticket_cast_and_city_async(eName, ticket))["city"]

    # /date
    async def on_message_search_event_by_date(self, date, _city=None, ignore_sold_out=False):
        try:
            date_obj = standardize_datetime(date, with_second=False, return_str=False)
        except ValueError:
            return "日期格式错误，请使用 YYYY-MM-DD 格式。\n例如：/date 2025-07-19"
        result_by_city = {}
        city_events_count = {}
        if self.updating:
            # 当数据正在更新时，等到数据全部更新完再继续
            await self._wait_for_data_update()
        for eid, event in self.events().items():
            try:
                event_start = standardize_datetime(event["start_time"], with_second=False, return_str=False)
                event_end = standardize_datetime(event["end_time"], with_second=False, return_str=False)
            except Exception:
                continue
            if not (event_start.date() <= date_obj.date() <= event_end.date()):
                continue
            for ticket in event.get("ticket_details", {}).values():
                if ignore_sold_out and ticket.get("left_ticket_count", 0)==0:
                    continue
                t_start = ticket.get("start_time")
                if not t_start:
                    continue
                try:
                    t_start = standardize_datetime(t_start, with_second=False, return_str=False)
                except Exception:
                    continue
                if t_start.date() != date_obj.date():
                    continue
                tInfo = extract_title_info(ticket.get("title", ""))
                event_title = tInfo['title'][1:-1]
                event_city = await self.get_ticket_city_async(event_title, ticket) or "未知城市"
                if _city:
                    if not event_city or _city not in event_city:
                        continue
                cast_str = await self.get_cast_artists_str_async(event_title, ticket, _city) or "无卡司信息"
                time_key = t_start.strftime("%H:%M")
                if event_city not in result_by_city:
                    result_by_city[event_city] = {}
                    result_by_city[event_city][time_key] = []
                    city_events_count[event_city] = 1
                elif time_key not in result_by_city[event_city]:
                    result_by_city[event_city][time_key] = []
                city_events_count[event_city] += 1
                result_by_city[event_city][time_key].append({
                    "event_title": tInfo['title'] + " " + tInfo["price"] + (f"(原价：{tInfo['full_price']})" if tInfo["full_price"] else ""),
                    "ticket_title": ticket.get("title", ""),
                    "cast": cast_str,
                    "left": ticket.get("left_ticket_count", "-"),
                    "total": ticket.get("total_ticket", "-"),
                })
        if not result_by_city:
            return f"{date} {_city or ''} 当天无呼啦圈学生票场次信息。"
        message = f"{date} {_city or ''} 呼啦圈学生票场次：\n"
        sorted_keys = sorted(city_events_count, key=lambda x: city_events_count[x], reverse=True)
        if "未知城市" in sorted_keys:
            sorted_keys.remove("未知城市")
            sorted_keys.append("未知城市")
        for city_key in sorted_keys:
            message += f"城市：{city_key}\n"
            for t in sorted(result_by_city[city_key].keys()):
                message += f"⏲️时间：{t}\n"
                for item in result_by_city[city_key][t]:
                    message += ("✨" if item['left'] > 0 else "❌") + f"{item['event_title']} 余票{item['left']}/{item['total']}" + " " + item["cast"] + "\n"
        message += f"\n数据更新时间: {self.data['update_time']}\n"
        return message
    
    

    async def generate_tickets_query_message(self, eid, show_cast=True, ignore_sold_out=False, refresh=False, show_ticket_id=False):  
        if not refresh:
            event_data = self.events().get(str(eid), None)
        else:
            await self._update_ticket_details_async(eid)
            event_data = self.events().get(str(eid), None)
        if event_data:
            title = event_data.get("title", "未知剧名")
            tickets_details = event_data.get("ticket_details", {})
            remaining_tickets = []
            for ticket in tickets_details.values():
                if ticket["status"] == "active":
                    if ticket["left_ticket_count"] > (0 if ignore_sold_out else -1):
                        remaining_tickets.append(ticket)
                elif ticket["status"] == "pending":
                    remaining_tickets.append(ticket)
            url = f"https://clubz.cloudsation.com/event/{eid}.html"
            message = await self.build_ticket_query_info_message(
                title, url, event_data, remaining_tickets, show_cast=show_cast, show_ticket_id=show_ticket_id
            )
            return message
        else:
            return "未找到该剧目的详细信息。"
    
    
    async def build_ticket_query_info_message(self, title, url, event_data, remaining_tickets, show_cast=False, show_ticket_id=False):
        # 获取更新时间
        update_time = event_data.get('update_time', '未知')

        # 获取剩余票务信息
        ticket_info_message, no_saoju_data, pending_t = await self._generate_ticket_info_message(remaining_tickets, show_cast, event_data, show_ticket_id)
        pending = pending_t[0]
        valid_from = pending_t[1] if pending else ""
        # 拼接消息
        message = ""
        message += f"剧名: {title}\n"
        message += f"购票链接：{url}\n"
        message += f"最后更新时间：{update_time}\n"
        if pending:
            message += f"🕰️即将开票，开票时间：{valid_from}\n一切数据若有官方来源以官方为准，这个时间可能会因为主办方调整而改变。\n"
        message += "剩余票务信息:\n"
        message += ticket_info_message
        if no_saoju_data:
            message += "\n⚠️未在扫剧网站上找到此剧卡司"
        message += f"\n数据更新时间: {self.data['update_time']}\n"
        return message

    async def build_single_ticket_info_str(self, ticket, show_cast, event_data, show_ticket_id):
        """
        根据ticket字典生成单条票务信息字符串。
        Args:
            ticket: 单个票务字典
            show_cast: 是否显示卡司
            eName: 剧名（用于查卡司）
            event_data: 事件数据（用于查城市）
            show_ticket_id: 是否显示票id
        Returns:
            (str, bool): 票务信息字符串, 是否无卡司数据
        """
        max_ticket_info_count = self.get_max_ticket_content_length([ticket])
        if ticket['status'] == 'active' and ticket['left_ticket_count'] > 0:
            ticket_status = "✨" 
        elif ticket["status"] == 'pending':
            v = ticket["valid_from"]
            v = v if v else "未知时间"
            ticket_status = f"🕰️"
        else:
            ticket_status = "❌"
        ticket_details = ljust_for_chinese(f"{ticket['title']} 余票{ticket['left_ticket_count']}/{ticket['total_ticket']}", max_ticket_info_count)
        if show_ticket_id:
            ticket_details = ' ' + ticket['id'] + ticket_details
        no_saoju_data = False
        if show_cast:
            cast_str = await self.get_cast_artists_str_async(ticket['title'], ticket, city=extract_city(event_data.get("location", "")))
            ticket_details += " " + cast_str
            if not cast_str:
                no_saoju_data = True
        text = ticket_status + ticket_details
        return text, no_saoju_data, (ticket["status"] == 'pending', ticket["valid_from"])

    async def _generate_ticket_info_message(self, remaining_tickets, show_cast, event_data, show_ticket_id):
        if not remaining_tickets:
            return "暂无余票。", True, (False, "")
        ticket_lines = []
        no_saoju_data = False
        pending_t = (False, "")
        for ticket in remaining_tickets:
            text, no_cast, pending_t = await self.build_single_ticket_info_str(ticket, show_cast, event_data, show_ticket_id)
            if no_cast:
                no_saoju_data = True
            ticket_lines.append(text)
        return ("\n".join(ticket_lines), no_saoju_data, pending_t)
    
    async def __update_ticket_dict_async(self):
        to_delete = []
        for ticket_id, event_id in self.data['ticket_id_to_event_id'].items():
            ticket = self.ticket(ticket_id, event_id)
            if not ticket:
                to_delete.append((event_id, ticket_id))
                continue
            if "end_time" not in ticket:
                continue
            end_time = standardize_datetime(ticket["end_time"], return_str=False)
            if datetime.now() > end_time:
                to_delete.append((event_id, ticket_id))
        for tup in to_delete:
            eid, tid = tup
            self.delete_ticket(tid, eid)
            self.data['ticket_id_to_event_id'].pop(tid, None)
            
    def update_ticket_dict_async(self):
        asyncio.create_task(self.__update_ticket_dict_async())
    
    def ticket(self, ticket_id, event_id=None):
        if not event_id:
            event_id = self.ticketID_to_eventID(ticket_id)
        if ticket_id not in self.ticket_details(event_id):
            return None
        return self.ticket_details(event_id)[ticket_id]
    
    def delete_ticket(self, ticket_id, event_id=None):
        if not event_id:
            event_id = self.ticketID_to_eventID(ticket_id)
        return self.data['events'][event_id]["ticket_details"].pop(ticket_id, None)
    
    def ticket_details(self, event_id):
        """根据eventid获取票务数据
        Args:
            event_id (str): 
        Returns:
            {
  ticket_id: {
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
}}
        """        
        return self.data['events'][event_id]["ticket_details"]
    
    def ticketID_to_eventID(self, ticket_id, none_value=0, raise_error=True):
        if ticket_id not in self.data["ticket_id_to_event_id"]:
            for e in self.events():
                for t in self.ticket_details(e).keys():
                    if t == ticket_id:
                        return e
        else:
            return self.data["ticket_id_to_event_id"][ticket_id]
        if raise_error:
            raise KeyError
        return none_value
    
    def verify_ticket_id(self, ticket_id):
        if isinstance(ticket_id, str):
            ticket_id = [ticket_id]
        denial = []
        yes: list = ticket_id
        for tid in ticket_id:
            if not self.ticketID_to_eventID(ticket_id, raise_error=False):
                denial.append(tid)
                yes.pop(tid, None)
        return yes, denial
            
            
    async def on_message_tickets_query(self, eName, ignore_sold_out=False, show_cast=True, refresh=False):
        result = []
        if self.updating:
            await self._wait_for_data_update()
        eName = eName.strip().lower()
        # 优先用别名系统生成检索名列表
        search_names = self.get_ordered_search_names(title=eName)
        for search_name in search_names:
            result = await self.search_eventID_by_name_async(search_name)
            if len(result) == 1:
                eid = result[0][0]
                Alias.set_no_response(eName, search_name, reset=True)
                return await self.generate_tickets_query_message(eid, show_cast=show_cast, ignore_sold_out=ignore_sold_out, refresh=refresh)
            elif len(result) > 1:
                queue = [f"{i}. {event[1]}" for i, event in enumerate(result, start=1)]
                return f"找到多个匹配的剧名，请重新以唯一的关键词查询：\n" + "\n".join(queue)
            else:
                Alias.set_no_response(eName, search_name, reset=False)
        return "未找到该剧目。"
        
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


    async def get_hlq_co_cast_event(self, co_casts, show_others=True):
        casts_data = await Saoju.request_co_casts_data(co_casts, show_others=show_others)
        message_id_list = []
        for event in casts_data:
            title = extract_text_in_brackets(event['title'], False)
            # 优先用别名系统查event_id
            event_id = None
            search_names = self.get_ordered_search_names(title=title)
            for name in search_names:
                result = await self.search_eventID_by_name_async(name)
                if len(result) == 1:
                    event_id = result[0][0]
                    break
            if event_id:
                event['event_id'] = event_id
                message_id_list.append(event)
        if self.updating:
            # 当数据正在更新时，等到数据全部更新完再继续
            await self._wait_for_data_update()
        tickets = []
        for event in message_id_list:
            # 获取对应的票务数据和卡司数据
            event_id = event['event_id']
            for ticket_id, ticket in self.ticket_details(event_id).items():
                if standardize_datetime_for_saoju(event["date"]) == ticket['start_time']:
                    tickets.append(ticket)
                    break
    
    
    def get_ordered_search_names(self, title=None, event_id=None):
        """
        根据event_id或title，结合别名系统，返回排序有意义的检索名（search_name）列表。
        优先级：
        1. 若event_id存在且在别名系统中，返回别名系统中该event_id的所有search_name（按添加顺序）。
        2. 若title存在且为别名（alias），查找其event_id并返回对应search_name列表。
        3. 若title本身为search_name，直接返回[title]。
        4. 否则返回空列表。
        """
        # 优先用event_id
        if event_id:
            event_id = str(event_id)
            search_names = Alias.data.get("event_to_names", {}).get(event_id)
            if search_names:
                return list(search_names)
        # 其次用title查alias
        if title:
            t = title.strip()
            # 1. 作为alias查event_id
            eid = Alias.get_event_id_by_alias(t)
            if eid:
                search_names = Alias.data.get("event_to_names", {}).get(eid)
                if search_names:
                    return list(search_names)
            # 2. 作为search_name查event_id
            eid2 = Alias.get_event_id_by_name(t)
            if eid2:
                search_names = Alias.data.get("event_to_names", {}).get(eid2)
                if search_names:
                    return list(search_names)
            # 3. title本身为search_name
            return [t]
        return []