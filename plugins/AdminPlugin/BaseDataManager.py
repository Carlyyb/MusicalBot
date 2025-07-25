import json
import os
import asyncio
import traceback
from ncatbot.utils.logger import get_log

log = get_log()

class BaseDataManager:
    
    def __init__(self, file_path, *args, **kwargs):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.work_path = "data/data_manager/"
        self.file_path = file_path or f"{self.work_path}{self.__class__.__name__}.json"
        self.data = {}
        self.updating = False
        self.__on_load()
        self.on_load(*args, **kwargs)
        self._initialized = True
        
    async def on_close(self):
        await self.save()

    def __on_load(self):
        try:
            self.updating = True
            if os.path.exists(self.file_path):
                self.load()
            elif not os.path.exists(self.work_path):
                os.makedirs(self.work_path)
                open(self.file_path, "w", encoding="utf-8").write(json.dumps({}))
            else:
                open(self.file_path, "w", encoding="utf-8").write(json.dumps({}))
            self.updating = False
        except Exception as e:
            self.updating = False
            traceback.print_exc()
            raise RuntimeError(self.__class__.__name__, f"加载持久化数据时出错: {e}")
        
    def load(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            try:
                self.data = json.load(f)
            except json.JSONDecodeError as e:
                self.data = {}
                raise

    async def save(self, on_close=False):
        """_summary_

        Raises:
            RuntimeError: _description_

        Returns:
            dict[str: bool]:  {"success":True, "updating":False}
        """
        try:
            if self.updating:
                if not on_close:
                    await self._wait_for_data_update()
                else:
                    return {"success":False, "updating":True}
            # 备份机制：保存前先备份原文件
            if os.path.exists(self.file_path):
                backup_path = self.file_path + ".bak"
                try:
                    # 如果已有备份，先删除
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    os.rename(self.file_path, backup_path)
                except Exception as e:
                    print(f"备份原数据文件失败: {e}")
            # 正式写入新数据
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
                return {"success":True, "updating":False}
        except Exception as e:
            traceback.print_exc()
            # 如果写入失败，尝试恢复备份
            backup_path = self.file_path + ".bak"
            if os.path.exists(backup_path):
                try:
                    os.rename(backup_path, self.file_path)
                    print("已自动恢复备份数据文件！")
                except Exception as e2:
                    print(f"恢复备份失败: {e2}")
            raise RuntimeError(f"保存持久化数据时出错: {e}")
        
    async def _wait_for_data_update(self):
        """
        等待数据更新完成，直到self.updating为False
        """
        while self.updating:
            await asyncio.sleep(0.1)
        
    def on_load(self, *args, **kwargs):
        pass
    
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
            print(f"Creating new instance of {cls.__name__}, instance_id: {id(cls._instance)}")
        else:
            print(f"Using existing instance of {cls.__name__}, instance_id: {id(cls._instance)}")
        return cls._instance
    
    def switch_updating(self, flag=None):
        if flag:
            self.updating = flag
        else:
            self.updating = not self.updating
