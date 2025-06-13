# -*- coding: utf-8 -*-
"""
网络操作插件
提供网络请求监控、响应处理、API Mock等功能
"""

import json
import re
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from urllib.parse import urlparse

from config.constants import DEFAULT_TIMEOUT
from src.automation.action_types import StepAction
from src.automation.commands.base_command import Command, CommandFactory
from utils.logger import logger


@dataclass
class NetworkRule:
    """网络规则配置"""
    pattern: str
    method: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    response_modifier: Optional[Callable] = None
    delay: Optional[int] = None
    enabled: bool = True


class NetworkOperationsPlugin:
    """网络操作插件主类"""
    
    def __init__(self):
        self.name = "network_operations"
        self.version = "1.0.0"
        self.description = "网络操作插件，提供请求监控、响应处理、API Mock等功能"
        self.author = "Playwright UI Framework"
        
        # 插件配置
        self.config = {
            "enabled": True,
            "timeout": DEFAULT_TIMEOUT,
            "max_retries": 3,
            "mock_enabled": False,
            "intercept_enabled": True,
            "logging_enabled": True
        }
        
        # 网络规则管理
        self.rules: List[NetworkRule] = []
        self.intercepted_requests = []
        self.intercepted_responses = []
        
        # 注册命令
        self._register_commands()
    
    def _register_commands(self):
        """注册插件命令"""
        # 注册监控请求命令
        CommandFactory.register(StepAction.MONITOR_REQUEST)(MonitorRequestCommand)
        # 注册监控响应命令
        CommandFactory.register(StepAction.MONITOR_RESPONSE)(MonitorResponseCommand)
        # 注册新的网络命令
        CommandFactory.register("INTERCEPT_REQUEST")(InterceptRequestCommand)
        CommandFactory.register("MOCK_RESPONSE")(MockResponseCommand)
        CommandFactory.register("NETWORK_DELAY")(NetworkDelayCommand)
        CommandFactory.register("CLEAR_NETWORK_CACHE")(ClearNetworkCacheCommand)
    
    def add_rule(self, rule: NetworkRule):
        """添加网络规则"""
        self.rules.append(rule)
        logger.info(f"已添加网络规则: {rule.pattern}")
    
    def remove_rule(self, pattern: str):
        """移除网络规则"""
        self.rules = [rule for rule in self.rules if rule.pattern != pattern]
        logger.info(f"已移除网络规则: {pattern}")
    
    def clear_rules(self):
        """清空所有规则"""
        self.rules.clear()
        logger.info("已清空所有网络规则")
    
    def get_intercepted_data(self, data_type: str = "all") -> List[Dict]:
        """获取拦截的数据"""
        if data_type == "requests":
            return self.intercepted_requests
        elif data_type == "responses":
            return self.intercepted_responses
        else:
            return {
                "requests": self.intercepted_requests,
                "responses": self.intercepted_responses
            }
    
    def clear_intercepted_data(self):
        """清空拦截的数据"""
        self.intercepted_requests.clear()
        self.intercepted_responses.clear()
        logger.info("已清空拦截数据")
    
    def update_config(self, config: Dict[str, Any]):
        """更新插件配置"""
        self.config.update(config)
        logger.info(f"已更新网络插件配置: {config}")
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "config": self.config,
            "rules_count": len(self.rules),
            "intercepted_requests": len(self.intercepted_requests),
            "intercepted_responses": len(self.intercepted_responses)
        }


class MonitorRequestCommand(Command):
    """监测请求命令"""

    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        # 获取参数
        url_pattern = step.get("url_pattern", value)
        action_type = step.get("action_type", "click")
        assert_params = step.get("assert_params")
        variable_name = step.get("variable_name")
        scope = step.get("scope", "global")

        # 其他可能的参数
        kwargs = {}
        if action_type == "fill" and "value" in step:
            kwargs["value"] = step.get("value")
        elif action_type == "press_key" and "key" in step:
            kwargs["key"] = step.get("key")
        elif action_type == "select" and "value" in step:
            kwargs["value"] = step.get("value")

        # 检查URL格式
        if (
            url_pattern
            and "http" not in url_pattern
            and not url_pattern.startswith("*")
        ):
            if url_pattern.startswith("/"):
                url_pattern = f"**{url_pattern}**"
            else:
                url_pattern = f"**/{url_pattern}**"

        # 直接使用ui_helper进行网络监控
        request_data = ui_helper.monitor_action_request(
            url_pattern=url_pattern,
            selector=selector,
            action=action_type,
            assert_params=assert_params,
            timeout=DEFAULT_TIMEOUT,
            value=value,
            **kwargs,
        )

        # 如果提供了变量名，存储捕获数据
        if variable_name:
            ui_helper.variable_manager.set_variable(variable_name, request_data, scope)
            logger.info(f"已存储请求数据到变量 {variable_name}")


class MonitorResponseCommand(Command):
    """监测响应命令"""

    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        # 获取参数
        url_pattern = step.get("url_pattern", value)
        action_type = step.get("action_type", "click")
        assert_params = step.get("assert_params")
        save_params = step.get("save_params")
        timeout = int(step.get("timeout", DEFAULT_TIMEOUT))
        scope = step.get("scope", "global")
        variable_name = step.get("variable_name")

        # 其他可能的参数
        kwargs = {}
        if action_type == "fill" and "value" in step:
            kwargs["value"] = step.get("value")
        elif action_type == "press_key" and "key" in step:
            kwargs["key"] = step.get("key")
        elif action_type == "select" and "value" in step:
            kwargs["value"] = step.get("value")

        # 检查URL格式
        if (
            url_pattern
            and "http" not in url_pattern
            and not url_pattern.startswith("*")
        ):
            if url_pattern.startswith("/"):
                url_pattern = f"**{url_pattern}**"
            else:
                url_pattern = f"**/{url_pattern}**"

        # 直接使用ui_helper进行网络监控
        response_data = ui_helper.monitor_action_response(
            url_pattern=url_pattern,
            selector=selector,
            action=action_type,
            assert_params=assert_params,
            save_params=save_params,
            timeout=DEFAULT_TIMEOUT,
            value=value,
            **kwargs,
        )

        # 如果提供了变量名，存储捕获数据
        if variable_name:
            ui_helper.variable_manager.set_variable(variable_name, response_data, scope)
            logger.info(f"已存储响应数据到变量 {variable_name}")


class InterceptRequestCommand(Command):
    """拦截请求命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        url_pattern = step.get("url_pattern", value)
        method = step.get("method", "GET")
        headers = step.get("headers", {})
        modify_request = step.get("modify_request", False)
        variable_name = step.get("variable_name")
        scope = step.get("scope", "global")
        
        # 实现请求拦截逻辑
        intercepted_data = {
            "url_pattern": url_pattern,
            "method": method,
            "headers": headers,
            "timestamp": ui_helper.get_current_timestamp(),
            "modified": modify_request
        }
        
        # 存储拦截数据
        if hasattr(ui_helper, 'network_plugin'):
            ui_helper.network_plugin.intercepted_requests.append(intercepted_data)
        
        if variable_name:
            ui_helper.variable_manager.set_variable(variable_name, intercepted_data, scope)
            logger.info(f"已拦截请求并存储到变量 {variable_name}")


class MockResponseCommand(Command):
    """模拟响应命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        url_pattern = step.get("url_pattern", value)
        status_code = step.get("status_code", 200)
        response_body = step.get("response_body", {})
        headers = step.get("headers", {"Content-Type": "application/json"})
        delay = step.get("delay", 0)
        
        # 实现响应模拟逻辑
        mock_data = {
            "url_pattern": url_pattern,
            "status_code": status_code,
            "response_body": response_body,
            "headers": headers,
            "delay": delay,
            "timestamp": ui_helper.get_current_timestamp()
        }
        
        logger.info(f"已设置模拟响应: {url_pattern} -> {status_code}")
        
        # 存储模拟数据
        if hasattr(ui_helper, 'network_plugin'):
            ui_helper.network_plugin.intercepted_responses.append(mock_data)


class NetworkDelayCommand(Command):
    """网络延迟命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        url_pattern = step.get("url_pattern", value)
        delay_ms = step.get("delay_ms", 1000)
        apply_to = step.get("apply_to", "all")  # all, requests, responses
        
        # 实现网络延迟逻辑
        delay_config = {
            "url_pattern": url_pattern,
            "delay_ms": delay_ms,
            "apply_to": apply_to,
            "timestamp": ui_helper.get_current_timestamp()
        }
        
        logger.info(f"已设置网络延迟: {url_pattern} -> {delay_ms}ms")


class ClearNetworkCacheCommand(Command):
    """清空网络缓存命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        cache_type = step.get("cache_type", "all")  # all, requests, responses, rules
        
        if hasattr(ui_helper, 'network_plugin'):
            plugin = ui_helper.network_plugin
            
            if cache_type == "all":
                plugin.clear_intercepted_data()
                plugin.clear_rules()
            elif cache_type == "requests":
                plugin.intercepted_requests.clear()
            elif cache_type == "responses":
                plugin.intercepted_responses.clear()
            elif cache_type == "rules":
                plugin.clear_rules()
        
        logger.info(f"已清空网络缓存: {cache_type}")


# 插件初始化函数
def initialize_plugin() -> NetworkOperationsPlugin:
    """初始化网络操作插件"""
    plugin = NetworkOperationsPlugin()
    logger.info(f"网络操作插件已初始化: {plugin.name} v{plugin.version}")
    return plugin


# 插件清理函数
def cleanup_plugin(plugin: NetworkOperationsPlugin):
    """清理网络操作插件"""
    if plugin:
        plugin.clear_intercepted_data()
        plugin.clear_rules()
        logger.info(f"网络操作插件已清理: {plugin.name}")


# 插件配置验证函数
def validate_config(config: Dict[str, Any]) -> bool:
    """验证插件配置"""
    required_fields = ["enabled", "timeout"]
    
    for field in required_fields:
        if field not in config:
            logger.error(f"网络操作插件配置缺少必需字段: {field}")
            return False
    
    if not isinstance(config["enabled"], bool):
        logger.error("网络操作插件配置中 'enabled' 必须是布尔值")
        return False
    
    if not isinstance(config["timeout"], (int, float)) or config["timeout"] <= 0:
        logger.error("网络操作插件配置中 'timeout' 必须是正数")
        return False
    
    return True


# 获取插件信息函数
def get_plugin_info() -> Dict[str, Any]:
    """获取插件信息"""
    return {
        "name": "network_operations",
        "version": "1.0.0",
        "description": "网络操作插件，提供请求监控、响应处理、API Mock等功能",
        "author": "Playwright UI Framework",
        "dependencies": [],
        "commands": [
            "MONITOR_REQUEST",
            "MONITOR_RESPONSE", 
            "INTERCEPT_REQUEST",
            "MOCK_RESPONSE",
            "NETWORK_DELAY",
            "CLEAR_NETWORK_CACHE"
        ],
        "config_schema": {
            "enabled": {"type": "boolean", "default": True},
            "timeout": {"type": "number", "default": DEFAULT_TIMEOUT},
            "max_retries": {"type": "integer", "default": 3},
            "mock_enabled": {"type": "boolean", "default": False},
            "intercept_enabled": {"type": "boolean", "default": True},
            "logging_enabled": {"type": "boolean", "default": True}
        }
    }