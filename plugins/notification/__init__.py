"""通知插件

提供多种通知方式的统一接口，支持钉钉、邮件、Webhook、Slack等多种通知渠道。

主要功能：
- 钉钉机器人通知
- 邮件通知
- Webhook通知
- Slack通知
- 微信企业号通知
- 短信通知
- 自定义通知提供者
- 通知模板管理
- 通知历史记录
- 批量通知
- 条件通知
- 通知重试机制
- 通知统计和监控
"""

from .plugin import NotificationPlugin

__version__ = "1.0.0"
__author__ = "Automation Team"
__description__ = "多渠道通知插件，支持钉钉、邮件、Webhook等多种通知方式"

__all__ = ["NotificationPlugin"]
