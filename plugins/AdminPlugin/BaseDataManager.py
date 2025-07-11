import json
import os
import traceback

class BaseDataManager:
    def __init__(self, file_path):
        self.work_path = "data/data_manager/"
        self.file_path = file_path or f"{self.work_path}{self.__class__.__name__}.json"
        self.data = {}
        self.updating = False
        self.on_load()
        
    def on_close(self):
        """卸载插件时的清理操作

        执行插件卸载前的清理工作,保存数据并注销事件处理器

        Raises:
            RuntimeError: 保存持久化数据失败时抛出
        """
        self.save()

    def on_load(self):
        """加载插件时的初始化操作

        执行插件加载时的初始化工作,加载数据

        Raises:
            RuntimeError: 读取持久化数据失败时抛出
        """
        try:
            if os.path.exists(self.file_path):
                self.load()
            elif not os.path.exists(self.work_path):
                os.makedirs(self.work_path)
                open(self.file_path, "w", encoding="utf-8").write(json.dumps({}))
            else:
                open(self.file_path, "w", encoding="utf-8").write(json.dumps({}))
        except Exception as e:
            traceback.print_exc()
            raise RuntimeError(self.__class__.__name__, f"加载持久化数据时出错: {e}")
        
    def load(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            try:
                self.data = json.load(f)
            except json.JSONDecodeError as e:
                self.data = {}
        self._check_data()
        
    def save(self):
        try:
            if self.updating:
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
        
    def _check_data(self):
        pass
