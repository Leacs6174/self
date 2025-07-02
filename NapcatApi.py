import requests

from typing import Dict, List


class NapcatManager:
    def __init__(self, base_url="http://localhost:8080", token=None):
        self.base_url = base_url
        self.token = token
        self.last_message_id = 0  # 跟踪最后处理的消息ID
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}" if token else None
        }

    def send_group_message(self, group_id: str, message: str) -> bool:
        """发送群消息"""
        url = f"{self.base_url}/send_group_msg"
        payload = {
            "group_id": group_id,
            "message": [{
                "type": "text",
                "data": {"text": message}
            }]
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "ok" and result.get("retcode") == 0:
                    return True
            return False
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False

    def get_recent_messages(self, count: int = 10) -> List[Dict]:
        """获取最近消息"""
        url = f"{self.base_url}/get_recent_contact"
        payload = {"count": count}

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "ok" and result.get("retcode") == 0:
                    return result.get("data", [])
            return []
        except Exception as e:
            print(f"获取消息失败: {e}")
            return []

    def filter_new_group_messages(self, messages: List[Dict]) -> List[Dict]:
        """过滤出新的群消息"""
        new_messages = []
        for msg in messages:
            # 只处理群消息 (chatType=1 可能是群聊，具体值需根据Napcat文档确认)
            if msg.get("chatType") == 1 and int(msg.get("msgId", 0)) > self.last_message_id:
                # 提取纯文本内容
                text_content = self.extract_text_content(msg.get("lastestMsg", {}).get("message", []))
                if text_content:
                    new_messages.append({
                        "message_id": int(msg["msgId"]),
                        "group_id": msg["peerUin"],
                        "content": text_content,
                        "sender": msg.get("sendNickName", "未知")
                    })
                    self.last_message_id = max(self.last_message_id, int(msg["msgId"]))
        return new_messages

    def extract_text_content(self, message_parts: List[Dict]) -> str:
        """从复合消息中提取纯文本内容"""
        text_parts = []
        for part in message_parts:
            if part.get("type") == "text":
                text_parts.append(part.get("data", {}).get("text", ""))
        return "".join(text_parts)