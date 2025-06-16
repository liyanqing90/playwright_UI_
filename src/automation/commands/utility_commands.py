"""
utility_commands - 合并的命令文件

合并了以下文件的命令:
- network_commands.py
- misc_commands.py
"""

from typing import Dict, Any

from config.constants import DEFAULT_TYPE_DELAY
from src.automation.action_types import StepAction
from src.automation.commands.base_command import Command, CommandFactory
from src.automation.utils import generate_faker_data, run_dynamic_script_from_path
from utils.logger import logger

# 检查插件是否可用
try:
    from src.core.plugin_compatibility import plugin_manager
    PLUGIN_AVAILABLE = True
except ImportError:
    PLUGIN_AVAILABLE = False

# 动态检查插件是否可用
def _get_plugin_command(plugin_name, command_class):
    """动态获取插件命令"""
    try:
        from src.core.plugin_compatibility import plugin_manager
        if plugin_name in plugin_manager.loaded_plugins:
            plugin_module = plugin_manager.loaded_plugins[plugin_name]
            if hasattr(plugin_module, command_class):
                return getattr(plugin_module, command_class)
    except Exception as e:
        logger.debug(f"Failed to get plugin command {plugin_name}.{command_class}: {e}")
    return None

@CommandFactory.register(StepAction.MONITOR_REQUEST)
class MonitorRequestCommand(Command):
    """监控网络请求命令 - 插件包装器"""
    
    def __init__(self):
        super().__init__()
    
    def execute(self, ui_helper, selector, value, step):
        """执行监控请求命令"""
        # 尝试使用插件实现
        plugin_command_class = _get_plugin_command('network_operations', 'MonitorRequestCommand')
        if plugin_command_class:
            try:
                plugin_command = plugin_command_class()
                return plugin_command.execute(ui_helper, selector, value, step)
            except Exception as e:
                logger.warning(f"Plugin command failed, falling back to legacy: {e}")
        
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
            # 不再传递整个 step 字典，而是只传递需要的参数
            # 从step中提取可能需要的其他参数
            timeout = step.get('timeout', None)
            wait_time = step.get('wait_time', None)
            include_headers = step.get('include_headers', False)
            include_body = step.get('include_body', True)

            logger.info(f"执行动作: {action_type} on {selector}")
                
            request_data = ui_helper.monitor_action_request(
                url_pattern=url_pattern,
                selector=selector,
                action=action_type,
                timeout=timeout
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
            # 标记异常已记录，避免重复记录
            setattr(e, "_logged", True)
            raise

@CommandFactory.register(StepAction.MONITOR_RESPONSE)
class MonitorResponseCommand(Command):
    """监控网络响应命令 - 插件包装器"""
    
    def __init__(self):
        super().__init__()
    
    def execute(self, ui_helper, selector, value, step):
        """执行监控响应命令"""
        # 尝试使用插件实现
        plugin_command_class = _get_plugin_command('network_operations', 'MonitorResponseCommand')
        if plugin_command_class:
            try:
                plugin_command = plugin_command_class()
                return plugin_command.execute(ui_helper, selector, value, step)
            except Exception as e:
                logger.warning(f"Plugin command failed, falling back to legacy: {e}")
        
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

@CommandFactory.register(StepAction.SCROLL_INTO_VIEW)
class ScrollIntoViewCommand(Command):
    """滚动到元素命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.scroll_into_view(selector=selector)

@CommandFactory.register(StepAction.SCROLL_TO)
class ScrollToCommand(Command):
    """滚动到位置命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        x = int(step.get("x", 0))
        y = int(step.get("y", 0))
        ui_helper.scroll_to(x=x, y=y)

@CommandFactory.register(StepAction.FOCUS)
class FocusCommand(Command):
    """聚焦命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.focus(selector=selector)

@CommandFactory.register(StepAction.BLUR)
class BlurCommand(Command):
    """失焦命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.blur(selector=selector)

@CommandFactory.register(StepAction.ENTER_FRAME)
class EnterFrameCommand(Command):
    """进入框架命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.enter_frame(selector=selector)

@CommandFactory.register(StepAction.ACCEPT_ALERT)
class AcceptAlertCommand(Command):
    """接受弹框命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.accept_alert(selector=selector, prompt_text=value)

@CommandFactory.register(StepAction.DISMISS_ALERT)
class DismissAlertCommand(Command):
    """取消弹框命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.dismiss_alert(selector=selector)

@CommandFactory.register(StepAction.EXECUTE_PYTHON)
class ExecutePythonCommand(Command):
    """执行Python命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        run_dynamic_script_from_path(value)

@CommandFactory.register(StepAction.FAKER)
class FakerCommand(Command):
    """生成数据命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        data_type = step.get("data_type")
        kwargs = {
            k: v
            for k, v in step.items()
            if k not in ["action", "data_type", "variable_name", "scope"]
        }

        if "variable_name" not in step:
            raise ValueError("步骤缺少必要参数: variable_name")

        # 生成数据
        value = generate_faker_data(data_type, **kwargs)
        ui_helper.store_variable(
            step["variable_name"], value, step.get("scope", "global")
        )

@CommandFactory.register(StepAction.KEYBOARD_SHORTCUT)
class KeyboardShortcutCommand(Command):
    """键盘快捷键命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        key_combination = step.get("key_combination", value)
        ui_helper.press_keyboard_shortcut(key_combination)

@CommandFactory.register(StepAction.KEYBOARD_PRESS)
class KeyboardPressCommand(Command):
    """全局按键命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        key = step.get("key", value)
        ui_helper.keyboard_press(key)

@CommandFactory.register(StepAction.KEYBOARD_TYPE)
class KeyboardTypeCommand(Command):
    """全局输入命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        text = step.get("text", value)
        delay = int(step.get("delay", DEFAULT_TYPE_DELAY))
        ui_helper.keyboard_type(text, delay)
