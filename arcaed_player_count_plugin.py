import json
import os
import datetime
import time
from NapcatApi import NapcatManager
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


# 定义机厅信息的数据类
@dataclass
class ArcadeInfo:
    aliases: List[str]  # 别名列表
    current_player_count: str  # 当前人数
    last_report_time: str  # 上次上报时间
    last_reporter: str  # 上次上报人


# 定义机厅管理器
class ArcadeManager:
    def __init__(self, filename="arcade_data.json", napcat_url="http://localhost:8080", napcat_token=None):
        self.filename = filename
        self.arcades: Dict[str, ArcadeInfo] = {}  # str：机厅标准名称；ArcadeInfo：该机厅所对应的类

        self.napcat = NapcatManager(base_url=napcat_url, token=napcat_token)

        # 如果文件存在则调用加载数据函数
        if os.path.exists(self.filename):
            self.load_data()

    # 加载数据文件
    def load_data(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.arcades = {}  # 清空内存中的机厅数据以准备用文件中读取的数据覆盖
                for name, info in data.items():
                    self.arcades[name] = ArcadeInfo(
                        aliases=info['aliases'],
                        current_player_count=info['current_player_count'],
                        last_report_time=info['last_report_time'],
                        last_reporter=info['last_reporter']
                    )
                print(f"成功加载了{len(self.arcades)}个机厅的数据喵")
        except Exception as e:
            print(f"数据加载失败了喵，错误代码是：{e}喵")
            self.arcades = {}

    # 存储数据文件函数
    def save_data(self):
        try:
            data = {}
            for name, info in self.arcades.items():
                data[name] = asdict(info)
            with open(self.filename, 'w', encoding='utf-8') as datafile:
                json.dump(data, datafile, indent=2, ensure_ascii=False)
            print(f"成功保存了{len(self.arcades)}个机厅的数据喵")
            return True
        except Exception as e:
            print(f"数据保存不上喵，错误代码是：{e}喵")
            return False

    # 消息捕获器
    def get_message(self) -> List[Dict]:
        """获取新消息"""
        # 获取最近10条消息
        recent_messages = self.napcat.get_recent_messages(count=10)
        # 过滤出新的群消息
        new_messages = self.napcat.filter_new_group_messages(recent_messages)
        return new_messages

    # 消息发送器
    def send_message(self, group_id: str, message: str) -> bool:
        """发送消息到指定群"""
        return self.napcat.send_group_message(group_id, message)

    # 消息播报（后台）
    def log_report(self, report: str, group_id: Optional[str] = None):
        heartbeat = "\033[5;33m[{0}]:\033[0m	{1}"
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(heartbeat.format(current_time, report))

    # 上报人获取器
    def get_reporter(self):
        return ""

    # 命令操作器
    def arcade_commander(self, command: str):
        current_hour = datetime.datetime.now().hour
        current_minute = datetime.datetime.now().minute

        if "创建机厅" in command:
            return 1

        elif "添加别名" in command:
            return 2

        elif "删除别名" in command:
            return 3

        # 查询人数
        elif "几人" in command:
            clean_command = command.replace("几人", "")
            for arcade_name in self.arcades:
                if clean_command in self.arcades[arcade_name].aliases or clean_command == arcade_name:
                    return 4
            return 0

        # 上报人数		格式：update xx机厅x人
        elif "update" in command:
            return 5

        # 每日清空机厅人数
        if current_hour == 0 and current_minute == 0:
            return 6

        return 0

    # 机厅创建器     #输入语法：创建机厅 机厅名称
    def arcade_adder(self, command: str):
        parts = command.split()
        if len(parts) != 2:
            self.send_message("输入格式有误喵，请重新检查喵")
        else:
            arcade_name = command.replace("创建机厅 ", "")
            self.arcades[arcade_name] = ArcadeInfo(
                aliases=[arcade_name],
                current_player_count="0",
                last_report_time="",
                last_reporter=self.get_reporter()
            )
            msg = "创建机厅 {} 成功了喵"
            self.send_message(msg.format(arcade_name))

    # 机厅别名添加器    # 输入语法：添加别名 机厅名称 机厅别名
    def alias_adder(self, command_add_alias: str):
        parts = command_add_alias.split()
        if len(parts) != 3:
            self.send_message("输入格式有误喵，请重新检查喵")
        else:
            arcade_name = command_add_alias.split()[1]
            added_alias = command_add_alias.split()[2]
            self.arcades[arcade_name].aliases.append(added_alias)
            msg = "对 {0} 添加别名 {1} 成功了喵"
            self.send_message(msg.format(arcade_name, added_alias))

    # 机厅别名删除器    # 输入语法：删除别名 机厅名称 机厅别名
    def alias_deleter(self, command_del_alias: str):
        parts = command_del_alias.split()
        if len(parts) != 3:
            self.send_message("输入格式有误喵，请重新检查喵")
        else:
            operated_arcade = parts[1]
            deleted_alias = parts[2]
            if operated_arcade not in self.arcades:
                self.send_message("找不到对应的机厅喵，请使用标准名称哦")
            if deleted_alias in self.arcades[operated_arcade].aliases:
                self.arcades[operated_arcade].aliases.remove(deleted_alias)
                self.send_message("删除成功了喵")
            else:
                self.send_message("找不到别名喵，可能已经被删过了哦")

    # 机厅人数查询器
    def get_player_count(self, uncleaned_alia: str):
        alia = uncleaned_alia.replace("几人", "")
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for arcade in self.arcades:
            if alia in self.arcades[arcade].aliases:
                if self.arcades[arcade].current_player_count != "0":
                    aser = "{0}有{1}人喵\n上次上报时间: {2}"
                    self.send_message(aser.format(alia, self.arcades[arcade].aliases.count(alia), current_time))
                else:
                    aser = "{}现在还没有人，或者还没人上报过，也许你可以去吧唧喵"
                    self.send_message(aser.format(alia))
            else:
                return 0
        return 0

    # 机厅人数上报器   #语法：update 机厅别名x人
    def report_player_count(self, command: str):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cleaned1_command = command.replace("update ", "")
        cleaned2_command = cleaned1_command.replace("人", "")

        for arcade in self.arcades:
            for alias in self.arcades[arcade].aliases:
                if alias in cleaned2_command:
                    player_count = cleaned2_command.replace(alias, "")
                    self.arcades[arcade].current_player_count = player_count
                    self.arcades[arcade].last_report_time = current_time
                    self.arcades[arcade].last_reporter = self.get_reporter()
                    aser = "更新成功了喵，{0}现在有{1}人"
                    self.send_message(aser.format(arcade, player_count))
                else:
                    self.send_message("找不到对应的机厅喵")

    # 零点清空机厅人数
    def player_count_clearer(self):
        for arcade in self.arcades:
            self.arcades[arcade].current_player_count = "0"
            self.arcades[arcade].last_report_time = ""
            self.arcades[arcade].last_reporter = ""
        return 0

    # 机厅操作器
    def report_arcade(self, message: Dict):

        command = message["content"]
        group_id = message["group_id"]

        self.current_group_id = group_id

        action = self.arcade_commander(command)

        if action == 1:  # 创建机厅
            self.arcade_adder(command)

        elif action == 2:  # 添加别名
            self.alias_adder(command)

        elif action == 3:  # 删除别名
            self.alias_deleter(command)

        elif action == 4:  # 查询人数
            self.get_player_count(command)

        elif action == 5:  # 上报人数
            self.report_player_count(command)

        elif action == 6:  # 自动清空当日人数
            self.player_count_clearer()

        # 保存当前信息至json
        self.save_data()
        return "保存成功了喵"


# 消息处理
class MessageProcessor:
    def __init__(self, napcat_url="http://localhost:8080", napcat_token=None):
        self.manager = ArcadeManager(
        filename = "arcade_data.json",
        napcat_url = napcat_url,
        napcat_token = napcat_token
        )
        self.running = True

    def run(self):
        try:
            while self.running:
                messages = self.manager.get_message()
                if not messages:
                    time.sleep(2)
                    continue

                for msg in messages:
                    try:
                        self.manager.report_arcade(msg)

                        # 日志记录（带群ID）
                        log_msg = f"处理来自 {msg['sender']} 的消息: {msg['content']}"
                        self.manager.log_report(log_msg)

                    except Exception as e:
                        self.manager.log_report(f"处理请求失败：{e}\n原始消息：{msg}")
                time.sleep(1)
        except KeyboardInterrupt:
            print("程序被用户终止")
        finally:
            self.shutdown()

    def shutdown(self):
        print("正在关闭消息处理器...")
        if hasattr(self.manager, 'close'):
            self.manager.close()
        print("资源已释放")


# 主程序
if __name__ == "__main__":
    # Napcat 配置
    NAPCAT_URL = "http://localhost:8080"  # Napcat 服务地址
    NAPCAT_TOKEN = "your_access_token"  # 访问令牌（如果有）

    processor = MessageProcessor(
        napcat_url = NAPCAT_URL,
        napcat_token = NAPCAT_TOKEN
    )
    processor.run()
