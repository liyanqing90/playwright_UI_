"""通知插件实现

提供多种通知方式的统一接口和管理功能。
"""

import base64
import hashlib
import hmac
import smtplib
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import requests

from src.automation.commands.base_command import Command, CommandFactory
from utils.logger import logger


class NotificationStatus(Enum):
    """通知状态"""
    PENDING = "pending"
    SENDING = "sending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"


class NotificationPriority(Enum):
    """通知优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(Enum):
    """通知类型"""
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    CARD = "card"


@dataclass
class NotificationMessage:
    """通知消息"""
    id: str
    title: str
    content: str
    type: NotificationType = NotificationType.TEXT
    priority: NotificationPriority = NotificationPriority.NORMAL
    recipients: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.recipients is None:
            self.recipients = []
        if self.attachments is None:
            self.attachments = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class NotificationResult:
    """通知结果"""
    message_id: str
    provider: str
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    response_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        if self.sent_at:
            data['sent_at'] = self.sent_at.isoformat()
        return data


class NotificationProvider(ABC):
    """通知提供者基类"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', True)
        
    @abstractmethod
    def send(self, message: NotificationMessage) -> NotificationResult:
        """发送通知"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置"""
        pass
    
    def is_available(self) -> bool:
        """检查提供者是否可用"""
        return self.enabled and self.validate_config()


class DingTalkProvider(NotificationProvider):
    """钉钉通知提供者"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("dingtalk", config)
        self.access_token = config.get('access_token')
        self.secret = config.get('secret')
        self.webhook_url = "https://oapi.dingtalk.com/robot/send"
        
    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.access_token and self.secret)
    
    def _generate_signature(self, timestamp: int) -> str:
        """生成签名"""
        secret_enc = self.secret.encode("utf-8")
        string_to_sign = f"{timestamp}\n{self.secret}"
        string_to_sign_enc = string_to_sign.encode("utf-8")
        hmac_code = hmac.new(
            secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
        ).digest()
        return quote_plus(base64.b64encode(hmac_code))
    
    def send(self, message: NotificationMessage) -> NotificationResult:
        """发送钉钉通知"""
        result = NotificationResult(
            message_id=message.id,
            provider=self.name,
            status=NotificationStatus.SENDING
        )
        
        try:
            timestamp = int(time.time() * 1000)
            sign = self._generate_signature(timestamp)
            
            url = f"{self.webhook_url}?access_token={self.access_token}&timestamp={timestamp}&sign={sign}"
            
            # 构建消息体
            if message.type == NotificationType.MARKDOWN:
                payload = {
                    "msgtype": "markdown",
                    "markdown": {
                        "title": message.title,
                        "text": message.content
                    }
                }
            else:
                payload = {
                    "msgtype": "text",
                    "text": {
                        "content": f"{message.title}\n{message.content}"
                    }
                }
            
            # 添加@功能
            if message.recipients:
                payload["at"] = {
                    "atMobiles": message.recipients,
                    "isAtAll": False
                }
            else:
                payload["at"] = {"isAtAll": False}
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            response_data = response.json()
            if response_data.get('errcode') == 0:
                result.status = NotificationStatus.SUCCESS
                result.sent_at = datetime.now()
            else:
                result.status = NotificationStatus.FAILED
                result.error_message = response_data.get('errmsg', '未知错误')
            
            result.response_data = response_data
            
        except Exception as e:
            result.status = NotificationStatus.FAILED
            result.error_message = str(e)
            logger.error(f"钉钉通知发送失败: {e}")
        
        return result


class EmailProvider(NotificationProvider):
    """邮件通知提供者"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("email", config)
        self.smtp_server = config.get('smtp_server')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username')
        self.password = config.get('password')
        self.from_email = config.get('from_email')
        self.use_tls = config.get('use_tls', True)
        
    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.smtp_server and self.username and self.password and self.from_email)
    
    def send(self, message: NotificationMessage) -> NotificationResult:
        """发送邮件通知"""
        result = NotificationResult(
            message_id=message.id,
            provider=self.name,
            status=NotificationStatus.SENDING
        )
        
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = message.title
            msg['From'] = self.from_email
            msg['To'] = ', '.join(message.recipients or [])
            
            # 添加邮件内容
            if message.type == NotificationType.HTML:
                part = MIMEText(message.content, 'html', 'utf-8')
            else:
                part = MIMEText(message.content, 'plain', 'utf-8')
            msg.attach(part)
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            result.status = NotificationStatus.SUCCESS
            result.sent_at = datetime.now()
            
        except Exception as e:
            result.status = NotificationStatus.FAILED
            result.error_message = str(e)
            logger.error(f"邮件通知发送失败: {e}")
        
        return result


class WebhookProvider(NotificationProvider):
    """Webhook通知提供者"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("webhook", config)
        self.url = config.get('url')
        self.method = config.get('method', 'POST')
        self.headers = config.get('headers', {})
        self.timeout = config.get('timeout', 30)
        
    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.url)
    
    def send(self, message: NotificationMessage) -> NotificationResult:
        """发送Webhook通知"""
        result = NotificationResult(
            message_id=message.id,
            provider=self.name,
            status=NotificationStatus.SENDING
        )
        
        try:
            # 构建请求数据
            payload = {
                'id': message.id,
                'title': message.title,
                'content': message.content,
                'type': message.type.value,
                'priority': message.priority.value,
                'recipients': message.recipients,
                'metadata': message.metadata,
                'timestamp': message.created_at.isoformat() if message.created_at else None
            }
            
            # 发送请求
            response = requests.request(
                method=self.method,
                url=self.url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result.status = NotificationStatus.SUCCESS
            result.sent_at = datetime.now()
            result.response_data = {
                'status_code': response.status_code,
                'response_text': response.text[:1000]  # 限制响应长度
            }
            
        except Exception as e:
            result.status = NotificationStatus.FAILED
            result.error_message = str(e)
            logger.error(f"Webhook通知发送失败: {e}")
        
        return result


class SlackProvider(NotificationProvider):
    """Slack通知提供者"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("slack", config)
        self.webhook_url = config.get('webhook_url')
        self.channel = config.get('channel')
        self.username = config.get('username', 'Automation Bot')
        self.icon_emoji = config.get('icon_emoji', ':robot_face:')
        
    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.webhook_url)
    
    def send(self, message: NotificationMessage) -> NotificationResult:
        """发送Slack通知"""
        result = NotificationResult(
            message_id=message.id,
            provider=self.name,
            status=NotificationStatus.SENDING
        )
        
        try:
            # 构建Slack消息
            payload = {
                'username': self.username,
                'icon_emoji': self.icon_emoji,
                'text': f"*{message.title}*\n{message.content}"
            }
            
            if self.channel:
                payload['channel'] = self.channel
            
            # 如果是Markdown类型，使用blocks格式
            if message.type == NotificationType.MARKDOWN:
                payload['blocks'] = [
                    {
                        'type': 'section',
                        'text': {
                            'type': 'mrkdwn',
                            'text': f"*{message.title}*\n{message.content}"
                        }
                    }
                ]
                del payload['text']
            
            response = requests.post(self.webhook_url, json=payload, timeout=30)
            response.raise_for_status()
            
            if response.text == 'ok':
                result.status = NotificationStatus.SUCCESS
                result.sent_at = datetime.now()
            else:
                result.status = NotificationStatus.FAILED
                result.error_message = response.text
            
        except Exception as e:
            result.status = NotificationStatus.FAILED
            result.error_message = str(e)
            logger.error(f"Slack通知发送失败: {e}")
        
        return result


class NotificationTemplate:
    """通知模板"""
    
    def __init__(self, name: str, template: str, type: NotificationType = NotificationType.TEXT):
        self.name = name
        self.template = template
        self.type = type
    
    def render(self, variables: Dict[str, Any]) -> str:
        """渲染模板"""
        try:
            return self.template.format(**variables)
        except KeyError as e:
            logger.warning(f"模板变量缺失: {e}")
            return self.template
        except Exception as e:
            logger.error(f"模板渲染失败: {e}")
            return self.template


class NotificationManager:
    """通知管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers: Dict[str, NotificationProvider] = {}
        self.templates: Dict[str, NotificationTemplate] = {}
        self.history: List[NotificationResult] = []
        self.lock = threading.RLock()
        self.retry_config = config.get('retry', {})
        
        # 初始化提供者
        self._init_providers()
        
        # 初始化模板
        self._init_templates()
        
        # 启动重试任务
        if self.retry_config.get('enabled', True):
            self._start_retry_task()
    
    def _init_providers(self) -> None:
        """初始化通知提供者"""
        providers_config = self.config.get('providers', {})
        
        # 钉钉提供者
        if 'dingtalk' in providers_config:
            self.providers['dingtalk'] = DingTalkProvider(providers_config['dingtalk'])
        
        # 邮件提供者
        if 'email' in providers_config:
            self.providers['email'] = EmailProvider(providers_config['email'])
        
        # Webhook提供者
        if 'webhook' in providers_config:
            self.providers['webhook'] = WebhookProvider(providers_config['webhook'])
        
        # Slack提供者
        if 'slack' in providers_config:
            self.providers['slack'] = SlackProvider(providers_config['slack'])
        
        logger.info(f"初始化了 {len(self.providers)} 个通知提供者")
    
    def _init_templates(self) -> None:
        """初始化通知模板"""
        templates_config = self.config.get('templates', {})
        
        for name, template_config in templates_config.items():
            template = NotificationTemplate(
                name=name,
                template=template_config.get('content', ''),
                type=NotificationType(template_config.get('type', 'text'))
            )
            self.templates[name] = template
        
        logger.info(f"初始化了 {len(self.templates)} 个通知模板")
    
    def send_notification(self, message: NotificationMessage, 
                         providers: Optional[List[str]] = None) -> List[NotificationResult]:
        """发送通知"""
        if providers is None:
            providers = list(self.providers.keys())
        
        results = []
        
        for provider_name in providers:
            provider = self.providers.get(provider_name)
            if not provider:
                logger.warning(f"通知提供者不存在: {provider_name}")
                continue
            
            if not provider.is_available():
                logger.warning(f"通知提供者不可用: {provider_name}")
                continue
            
            try:
                result = provider.send(message)
                results.append(result)
                
                with self.lock:
                    self.history.append(result)
                
                logger.info(f"通知发送完成: {provider_name} - {result.status.value}")
                
            except Exception as e:
                error_result = NotificationResult(
                    message_id=message.id,
                    provider=provider_name,
                    status=NotificationStatus.FAILED,
                    error_message=str(e)
                )
                results.append(error_result)
                
                with self.lock:
                    self.history.append(error_result)
                
                logger.error(f"通知发送异常: {provider_name} - {e}")
        
        return results
    
    def send_with_template(self, template_name: str, variables: Dict[str, Any],
                          title: str, providers: Optional[List[str]] = None,
                          priority: NotificationPriority = NotificationPriority.NORMAL,
                          recipients: Optional[List[str]] = None) -> List[NotificationResult]:
        """使用模板发送通知"""
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"通知模板不存在: {template_name}")
        
        content = template.render(variables)
        
        message = NotificationMessage(
            id=f"msg_{int(time.time() * 1000)}",
            title=title,
            content=content,
            type=template.type,
            priority=priority,
            recipients=recipients
        )
        
        return self.send_notification(message, providers)
    
    def get_provider_status(self) -> Dict[str, bool]:
        """获取提供者状态"""
        return {name: provider.is_available() for name, provider in self.providers.items()}
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取通知历史"""
        with self.lock:
            recent_history = self.history[-limit:] if limit > 0 else self.history
            return [result.to_dict() for result in recent_history]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取通知统计"""
        with self.lock:
            total = len(self.history)
            if total == 0:
                return {
                    'total': 0,
                    'success_rate': 0,
                    'provider_stats': {},
                    'status_stats': {}
                }
            
            success_count = sum(1 for r in self.history if r.status == NotificationStatus.SUCCESS)
            
            # 按提供者统计
            provider_stats = {}
            for result in self.history:
                provider = result.provider
                if provider not in provider_stats:
                    provider_stats[provider] = {'total': 0, 'success': 0}
                provider_stats[provider]['total'] += 1
                if result.status == NotificationStatus.SUCCESS:
                    provider_stats[provider]['success'] += 1
            
            # 按状态统计
            status_stats = {}
            for result in self.history:
                status = result.status.value
                status_stats[status] = status_stats.get(status, 0) + 1
            
            return {
                'total': total,
                'success_rate': success_count / total,
                'provider_stats': provider_stats,
                'status_stats': status_stats
            }
    
    def cleanup_history(self, days: int = 30) -> int:
        """清理历史记录"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self.lock:
            original_count = len(self.history)
            self.history = [
                result for result in self.history 
                if result.sent_at and result.sent_at > cutoff_date
            ]
            cleaned_count = original_count - len(self.history)
        
        if cleaned_count > 0:
            logger.info(f"清理了 {cleaned_count} 条通知历史记录")
        
        return cleaned_count
    
    def _start_retry_task(self) -> None:
        """启动重试任务"""
        def retry_task():
            while True:
                try:
                    interval = self.retry_config.get('interval', 300)  # 5分钟
                    time.sleep(interval)
                    
                    max_retries = self.retry_config.get('max_retries', 3)
                    
                    with self.lock:
                        failed_results = [
                            result for result in self.history
                            if result.status == NotificationStatus.FAILED
                            and result.retry_count < max_retries
                        ]
                    
                    for result in failed_results:
                        # 这里可以实现重试逻辑
                        # 由于需要原始消息，暂时跳过自动重试
                        pass
                        
                except Exception as e:
                    logger.error(f"重试任务错误: {e}")
        
        retry_thread = threading.Thread(target=retry_task, daemon=True)
        retry_thread.start()
        logger.info("通知重试任务已启动")


class NotificationPlugin:
    """通知插件"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.notification_manager = NotificationManager(self.config)
        
        # 注册命令
        self._register_commands()
    
    def _register_commands(self) -> None:
        """注册命令"""
        # 基础通知命令
        CommandFactory.register('send_notification')(SendNotificationCommand)
        CommandFactory.register('send_template_notification')(SendTemplateNotificationCommand)
        CommandFactory.register('send_dingtalk')(SendDingTalkCommand)
        CommandFactory.register('send_email')(SendEmailCommand)
        CommandFactory.register('send_webhook')(SendWebhookCommand)
        CommandFactory.register('send_slack')(SendSlackCommand)
        
        # 批量通知命令
        CommandFactory.register('send_batch_notification')(SendBatchNotificationCommand)
        CommandFactory.register('send_conditional_notification')(SendConditionalNotificationCommand)
        
        # 管理命令
        CommandFactory.register('get_notification_status')(GetNotificationStatusCommand)
        CommandFactory.register('get_notification_history')(GetNotificationHistoryCommand)
        CommandFactory.register('get_notification_stats')(GetNotificationStatsCommand)
        CommandFactory.register('cleanup_notification_history')(CleanupNotificationHistoryCommand)


# 通知命令实现
class SendNotificationCommand(Command):
    """发送通知命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        title = step.get("title", "通知")
        content = step.get("content", "")
        providers = step.get("providers")
        priority = step.get("priority", "normal")
        recipients = step.get("recipients")
        notification_type = step.get("type", "text")
        metadata = step.get("metadata", {})
        
        plugin = getattr(ui_helper, 'notification_plugin', None)
        if not plugin:
            raise RuntimeError("通知插件未初始化")
        
        message = NotificationMessage(
            id=f"msg_{int(time.time() * 1000)}",
            title=title,
            content=content,
            type=NotificationType(notification_type),
            priority=NotificationPriority(priority),
            recipients=recipients,
            metadata=metadata
        )
        
        results = plugin.notification_manager.send_notification(message, providers)
        
        # 存储结果
        target_var = step.get("target_variable", "notification_results")
        if hasattr(ui_helper, 'storage_plugin'):
            ui_helper.storage_plugin.variable_manager.set_variable(
                target_var, [result.to_dict() for result in results], "global"
            )
        
        logger.info(f"发送通知完成: {len(results)} 个结果")


class SendTemplateNotificationCommand(Command):
    """发送模板通知命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        template_name = step.get("template_name")
        variables = step.get("variables", {})
        title = step.get("title", "通知")
        providers = step.get("providers")
        priority = step.get("priority", "normal")
        recipients = step.get("recipients")
        
        plugin = getattr(ui_helper, 'notification_plugin', None)
        if not plugin:
            raise RuntimeError("通知插件未初始化")
        
        results = plugin.notification_manager.send_with_template(
            template_name=template_name,
            variables=variables,
            title=title,
            providers=providers,
            priority=NotificationPriority(priority),
            recipients=recipients
        )
        
        # 存储结果
        target_var = step.get("target_variable", "notification_results")
        if hasattr(ui_helper, 'storage_plugin'):
            ui_helper.storage_plugin.variable_manager.set_variable(
                target_var, [result.to_dict() for result in results], "global"
            )
        
        logger.info(f"发送模板通知完成: {template_name}")


class SendDingTalkCommand(Command):
    """发送钉钉通知命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        title = step.get("title", "钉钉通知")
        content = step.get("content", "")
        at_mobiles = step.get("at_mobiles")
        is_markdown = step.get("is_markdown", False)
        
        plugin = getattr(ui_helper, 'notification_plugin', None)
        if not plugin:
            raise RuntimeError("通知插件未初始化")
        
        message = NotificationMessage(
            id=f"dingtalk_{int(time.time() * 1000)}",
            title=title,
            content=content,
            type=NotificationType.MARKDOWN if is_markdown else NotificationType.TEXT,
            recipients=at_mobiles
        )
        
        results = plugin.notification_manager.send_notification(message, ['dingtalk'])
        
        # 存储结果
        target_var = step.get("target_variable", "dingtalk_result")
        if hasattr(ui_helper, 'storage_plugin') and results:
            ui_helper.storage_plugin.variable_manager.set_variable(
                target_var, results[0].to_dict(), "global"
            )
        
        logger.info(f"发送钉钉通知完成: {results[0].status.value if results else '无结果'}")


class SendEmailCommand(Command):
    """发送邮件通知命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        title = step.get("title", "邮件通知")
        content = step.get("content", "")
        recipients = step.get("recipients", [])
        is_html = step.get("is_html", False)
        
        plugin = getattr(ui_helper, 'notification_plugin', None)
        if not plugin:
            raise RuntimeError("通知插件未初始化")
        
        message = NotificationMessage(
            id=f"email_{int(time.time() * 1000)}",
            title=title,
            content=content,
            type=NotificationType.HTML if is_html else NotificationType.TEXT,
            recipients=recipients
        )
        
        results = plugin.notification_manager.send_notification(message, ['email'])
        
        # 存储结果
        target_var = step.get("target_variable", "email_result")
        if hasattr(ui_helper, 'storage_plugin') and results:
            ui_helper.storage_plugin.variable_manager.set_variable(
                target_var, results[0].to_dict(), "global"
            )
        
        logger.info(f"发送邮件通知完成: {results[0].status.value if results else '无结果'}")


class SendWebhookCommand(Command):
    """发送Webhook通知命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        title = step.get("title", "Webhook通知")
        content = step.get("content", "")
        metadata = step.get("metadata", {})
        
        plugin = getattr(ui_helper, 'notification_plugin', None)
        if not plugin:
            raise RuntimeError("通知插件未初始化")
        
        message = NotificationMessage(
            id=f"webhook_{int(time.time() * 1000)}",
            title=title,
            content=content,
            type=NotificationType.JSON,
            metadata=metadata
        )
        
        results = plugin.notification_manager.send_notification(message, ['webhook'])
        
        # 存储结果
        target_var = step.get("target_variable", "webhook_result")
        if hasattr(ui_helper, 'storage_plugin') and results:
            ui_helper.storage_plugin.variable_manager.set_variable(
                target_var, results[0].to_dict(), "global"
            )
        
        logger.info(f"发送Webhook通知完成: {results[0].status.value if results else '无结果'}")


class SendSlackCommand(Command):
    """发送Slack通知命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        title = step.get("title", "Slack通知")
        content = step.get("content", "")
        channel = step.get("channel")
        is_markdown = step.get("is_markdown", False)
        
        plugin = getattr(ui_helper, 'notification_plugin', None)
        if not plugin:
            raise RuntimeError("通知插件未初始化")
        
        message = NotificationMessage(
            id=f"slack_{int(time.time() * 1000)}",
            title=title,
            content=content,
            type=NotificationType.MARKDOWN if is_markdown else NotificationType.TEXT,
            metadata={'channel': channel} if channel else {}
        )
        
        results = plugin.notification_manager.send_notification(message, ['slack'])
        
        # 存储结果
        target_var = step.get("target_variable", "slack_result")
        if hasattr(ui_helper, 'storage_plugin') and results:
            ui_helper.storage_plugin.variable_manager.set_variable(
                target_var, results[0].to_dict(), "global"
            )
        
        logger.info(f"发送Slack通知完成: {results[0].status.value if results else '无结果'}")


class SendBatchNotificationCommand(Command):
    """发送批量通知命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        notifications = step.get("notifications", [])
        providers = step.get("providers")
        
        plugin = getattr(ui_helper, 'notification_plugin', None)
        if not plugin:
            raise RuntimeError("通知插件未初始化")
        
        all_results = []
        
        for i, notification in enumerate(notifications):
            message = NotificationMessage(
                id=f"batch_{int(time.time() * 1000)}_{i}",
                title=notification.get("title", f"批量通知 {i+1}"),
                content=notification.get("content", ""),
                type=NotificationType(notification.get("type", "text")),
                priority=NotificationPriority(notification.get("priority", "normal")),
                recipients=notification.get("recipients")
            )
            
            results = plugin.notification_manager.send_notification(
                message, notification.get("providers") or providers
            )
            all_results.extend(results)
        
        # 存储结果
        target_var = step.get("target_variable", "batch_notification_results")
        if hasattr(ui_helper, 'storage_plugin'):
            ui_helper.storage_plugin.variable_manager.set_variable(
                target_var, [result.to_dict() for result in all_results], "global"
            )
        
        logger.info(f"发送批量通知完成: {len(notifications)} 条通知, {len(all_results)} 个结果")


class SendConditionalNotificationCommand(Command):
    """发送条件通知命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        condition = step.get("condition")
        title = step.get("title", "条件通知")
        content = step.get("content", "")
        providers = step.get("providers")
        
        # 评估条件
        if condition:
            # 这里可以实现条件评估逻辑
            # 暂时简单处理
            should_send = bool(condition)
        else:
            should_send = True
        
        if not should_send:
            logger.info("条件不满足，跳过通知发送")
            return
        
        plugin = getattr(ui_helper, 'notification_plugin', None)
        if not plugin:
            raise RuntimeError("通知插件未初始化")
        
        message = NotificationMessage(
            id=f"conditional_{int(time.time() * 1000)}",
            title=title,
            content=content,
            type=NotificationType(step.get("type", "text")),
            priority=NotificationPriority(step.get("priority", "normal")),
            recipients=step.get("recipients")
        )
        
        results = plugin.notification_manager.send_notification(message, providers)
        
        # 存储结果
        target_var = step.get("target_variable", "conditional_notification_results")
        if hasattr(ui_helper, 'storage_plugin'):
            ui_helper.storage_plugin.variable_manager.set_variable(
                target_var, [result.to_dict() for result in results], "global"
            )
        
        logger.info(f"发送条件通知完成: {len(results)} 个结果")


class GetNotificationStatusCommand(Command):
    """获取通知状态命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        target_var = step.get("target_variable", "notification_status")
        
        plugin = getattr(ui_helper, 'notification_plugin', None)
        if not plugin:
            raise RuntimeError("通知插件未初始化")
        
        status = plugin.notification_manager.get_provider_status()
        
        if hasattr(ui_helper, 'storage_plugin'):
            ui_helper.storage_plugin.variable_manager.set_variable(
                target_var, status, "global"
            )
        
        logger.info(f"获取通知状态: {status}")


class GetNotificationHistoryCommand(Command):
    """获取通知历史命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        limit = step.get("limit", 100)
        target_var = step.get("target_variable", "notification_history")
        
        plugin = getattr(ui_helper, 'notification_plugin', None)
        if not plugin:
            raise RuntimeError("通知插件未初始化")
        
        history = plugin.notification_manager.get_history(limit)
        
        if hasattr(ui_helper, 'storage_plugin'):
            ui_helper.storage_plugin.variable_manager.set_variable(
                target_var, history, "global"
            )
        
        logger.info(f"获取通知历史: {len(history)} 条记录")


class GetNotificationStatsCommand(Command):
    """获取通知统计命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        target_var = step.get("target_variable", "notification_stats")
        
        plugin = getattr(ui_helper, 'notification_plugin', None)
        if not plugin:
            raise RuntimeError("通知插件未初始化")
        
        stats = plugin.notification_manager.get_statistics()
        
        if hasattr(ui_helper, 'storage_plugin'):
            ui_helper.storage_plugin.variable_manager.set_variable(
                target_var, stats, "global"
            )
        
        logger.info(f"获取通知统计: 总计 {stats['total']} 条，成功率 {stats['success_rate']:.2%}")


class CleanupNotificationHistoryCommand(Command):
    """清理通知历史命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        days = step.get("days", 30)
        target_var = step.get("target_variable", "cleanup_count")
        
        plugin = getattr(ui_helper, 'notification_plugin', None)
        if not plugin:
            raise RuntimeError("通知插件未初始化")
        
        count = plugin.notification_manager.cleanup_history(days)
        
        if hasattr(ui_helper, 'storage_plugin'):
            ui_helper.storage_plugin.variable_manager.set_variable(
                target_var, count, "global"
            )
        
        logger.info(f"清理通知历史: {count} 条记录")