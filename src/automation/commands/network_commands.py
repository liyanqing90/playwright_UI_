# -*- coding: utf-8 -*-
"""
网络相关命令模块 - 已迁移到插件系统

注意：此模块已被重构为插件系统的一部分。
新的网络操作功能请使用 plugins/network_operations/ 插件。

为了保持向后兼容性，此文件保留了原有的命令注册，
但实际功能已委托给插件实现。
"""

from src.automation.commands.base_command import Command, CommandFactory
from src.automation.action_types import StepAction
from utils.logger import logger

# 尝试导入插件，如果插件不可用则使用原有实现
try:
    from plugins.network_operations.plugin import (
        MonitorRequestCommand as PluginMonitorRequestCommand,
        MonitorResponseCommand as PluginMonitorResponseCommand,
        initialize_plugin,
        cleanup_plugin
    )
    PLUGIN_AVAILABLE = True
    logger.info("网络操作插件已加载，使用插件实现")
except ImportError as e:
    PLUGIN_AVAILABLE = False
    logger.warning(f"网络操作插件不可用，使用原有实现: {e}")


@CommandFactory.register(StepAction.MONITOR_REQUEST)
class MonitorRequestCommand(Command):
    """监控网络请求命令 - 插件包装器"""
    
    def __init__(self):
        super().__init__()
        self._plugin_command = None
        if PLUGIN_AVAILABLE:
            self._plugin_command = PluginMonitorRequestCommand()
    
    def execute(self, ui_helper, selector, value, step):
        """执行监控请求命令"""
        if self._plugin_command:
            # 使用插件实现
            return self._plugin_command.execute(ui_helper, selector, value, step)
        else:
            # 使用原有实现
            return self._legacy_execute(ui_helper, selector, value, step)
    
    def _legacy_execute(self, ui_helper, selector, value, step):
        """原有的监控请求实现"""
        try:
            url_pattern = step.get('url_pattern', value)
            action_type = step.get('action_type', 'click')
            variable_name = step.get('variable_name')
            scope = step.get('scope', 'global')
            
            logger.info(f"开始监控请求: {url_pattern}")
            
            # 执行动作并监控请求
            request_data = ui_helper.monitor_action_request(
                selector=selector,
                action_type=action_type,
                url_pattern=url_pattern,
                **step
            )
            
            # 保存请求数据到变量
            if variable_name and request_data:
                ui_helper.variable_manager.set_variable(
                    variable_name, 
                    request_data, 
                    scope=scope
                )
                logger.info(f"请求数据已保存到变量: {variable_name}")
            
            return request_data
            
        except Exception as e:
            logger.error(f"监控请求失败: {e}")
            raise


@CommandFactory.register(StepAction.MONITOR_RESPONSE)
class MonitorResponseCommand(Command):
    """监控网络响应命令 - 插件包装器"""
    
    def __init__(self):
        super().__init__()
        self._plugin_command = None
        if PLUGIN_AVAILABLE:
            self._plugin_command = PluginMonitorResponseCommand()
    
    def execute(self, ui_helper, selector, value, step):
        """执行监控响应命令"""
        if self._plugin_command:
            # 使用插件实现
            return self._plugin_command.execute(ui_helper, selector, value, step)
        else:
            # 使用原有实现
            return self._legacy_execute(ui_helper, selector, value, step)
    
    def _legacy_execute(self, ui_helper, selector, value, step):
        """原有的监控响应实现"""
        try:
            url_pattern = step.get('url_pattern', value)
            action_type = step.get('action_type', 'click')
            assert_params = step.get('assert_params', {})
            save_params = step.get('save_params', [])
            variable_name = step.get('variable_name')
            timeout = step.get('timeout', 30000)
            
            logger.info(f"开始监控响应: {url_pattern}")
            
            # 执行动作并监控响应
            response_data = ui_helper.monitor_action_response(
                selector=selector,
                action_type=action_type,
                url_pattern=url_pattern,
                timeout=timeout,
                **step
            )
            
            # 断言响应数据
            if assert_params and response_data:
                for key, expected_value in assert_params.items():
                    actual_value = response_data.get(key)
                    if actual_value != expected_value:
                        raise AssertionError(
                            f"响应断言失败: {key} = {actual_value}, 期望: {expected_value}"
                        )
                logger.info("响应断言通过")
            
            # 保存响应数据的特定字段到变量
            if save_params and response_data:
                for param in save_params:
                    path = param.get('path')
                    var_name = param.get('variable_name')
                    if path and var_name:
                        # 从响应数据中提取指定路径的值
                        value_to_save = self._extract_value_by_path(response_data, path)
                        if value_to_save is not None:
                            ui_helper.variable_manager.set_variable(
                                var_name, 
                                value_to_save, 
                                scope=param.get('scope', 'global')
                            )
                            logger.info(f"响应字段已保存到变量: {var_name} = {value_to_save}")
            
            # 保存完整响应数据到变量
            if variable_name and response_data:
                ui_helper.variable_manager.set_variable(
                    variable_name, 
                    response_data, 
                    scope=step.get('scope', 'global')
                )
                logger.info(f"响应数据已保存到变量: {variable_name}")
            
            return response_data
            
        except Exception as e:
            logger.error(f"监控响应失败: {e}")
            raise
    
    def _extract_value_by_path(self, data, path):
        """从数据中按路径提取值"""
        try:
            keys = path.split('.')
            current = data
            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key)
                elif isinstance(current, list) and key.isdigit():
                    index = int(key)
                    current = current[index] if 0 <= index < len(current) else None
                else:
                    return None
                
                if current is None:
                    break
            
            return current
        except Exception:
            return None


# 如果插件可用，也注册插件的扩展命令
if PLUGIN_AVAILABLE:
    try:
        from plugins.network_operations.plugin import (
            InterceptRequestCommand,
            MockResponseCommand,
            NetworkDelayCommand,
            ClearNetworkCacheCommand
        )
        
        # 使用装饰器方式注册扩展命令
        @CommandFactory.register(["intercept_request"])
        class InterceptRequestCommandWrapper(InterceptRequestCommand):
            pass
            
        @CommandFactory.register(["mock_response"])
        class MockResponseCommandWrapper(MockResponseCommand):
            pass
            
        @CommandFactory.register(["network_delay"])
        class NetworkDelayCommandWrapper(NetworkDelayCommand):
            pass
            
        @CommandFactory.register(["clear_network_cache"])
        class ClearNetworkCacheCommandWrapper(ClearNetworkCacheCommand):
            pass
        
        logger.info("网络操作插件的扩展命令已注册")
    except ImportError as e:
        logger.warning(f"无法注册网络操作插件的扩展命令: {e}")
