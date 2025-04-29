import base64
import hashlib
import hmac
import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

import requests


class DingTalkNotifier:
    def __init__(self, access_token: str, secret: str):
        self.access_token = access_token
        self.secret = secret
        self.webhook_url = "https://oapi.dingtalk.com/robot/send"

    def _generate_signature(self, timestamp: int) -> str:
        secret_enc = self.secret.encode("utf-8")
        string_to_sign = f"{timestamp}\n{self.secret}"
        string_to_sign_enc = string_to_sign.encode("utf-8")
        hmac_code = hmac.new(
            secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
        ).digest()
        return quote_plus(base64.b64encode(hmac_code))

    def send_message(self, title: str, text: str, at_all=False):
        timestamp = int(time.time() * 1000)
        sign = self._generate_signature(timestamp)

        url = f"{self.webhook_url}?access_token={self.access_token}&timestamp={timestamp}&sign={sign}"

        message = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": text},
            "at": {"isAtAll": False},
        }
        print("发送报告")
        print(text)
        #
        response = requests.post(url, json=message)
        # response.raise_for_status()


class ReportStorage:
    def __init__(self, base_dir="reports"):
        self.history_dir = Path(base_dir) / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def save_report(self, report_data: dict):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.history_dir / f"report_{timestamp}.json"

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)


class ReportNotifier:
    def __init__(self, dingtalk_token: str, dingtalk_secret: str):
        self.dingtalk = DingTalkNotifier(dingtalk_token, dingtalk_secret)
        self.storage = ReportStorage()

    def format_report_message(self, report_data: dict) -> str:
        from utils.config import Config

        config = Config()
        disposition_part = [
            "#### 测试配置",
            f"- 浏览器：{config.browser.value}",
            f"- 运行模式：{'有头模式' if config.headed else '无头模式'}",
            f"- 运行环境：{config.env.value}",
            f"- 项目：{config.project.value}",
            f"- 用例标记：{getattr(config, 'marker', '无')}\n",
        ]
        overview_part = [
            "#### 测试概况",
            f"- 总用例数：{report_data['total_tests']}",
            f"- 通过率：{report_data['passed'] / report_data['total_tests']:.2%}",
            f"- 失败率：{report_data['failed'] / report_data['total_tests']:.2%}",
            f"- 跳过率：{report_data['skipped'] / report_data['total_tests']:.2%}",
            f"- 总耗时：{report_data['duration']}秒\n",
        ]
        message_parts = disposition_part + overview_part

        if report_data["failed"] > 0:
            message_parts.extend(
                ["#### 失败详情\n", self._format_failures(report_data["failures"])]
            )

        return "\n".join(message_parts)

    def _format_failures(self, failures: list) -> str:
        if not failures:
            return "无失败详情"
        failure_msgs = [
            f"- {failure.get('test_case', '未知用例')}: {failure.get('reason', '未知原因')}"
            for failure in failures
        ]
        return "\n".join(failure_msgs)  # 使用双换行符确保钉钉markdown格式正确

    def notify(self, report_data: dict):
        title = f"测试报告 - {report_data['environment']}"
        text = self.format_report_message(report_data)
        self.dingtalk.send_message(title, text)
        self.storage.save_report(report_data)
