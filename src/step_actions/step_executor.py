"""
步骤执行器的核心实现
"""

from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Dict, Any, List

import allure

from constants import DEFAULT_TIMEOUT, DEFAULT_TYPE_DELAY
from src.step_actions.action_types import StepAction

# 导入命令模式执行器
from src.step_actions.command_executor import execute_action_with_command
from src.step_actions.flow_control import (
    execute_condition,
    execute_loop,
    evaluate_expression,
)
from src.step_actions.module_handler import execute_module
from src.step_actions.network_monitor import (
    monitor_action_request,
    monitor_action_response,
)
from src.step_actions.utils import generate_faker_data, run_dynamic_script_from_path
from utils.logger import logger
from utils.variable_manager import VariableManager


# 导入所有命令类


class StepExecutor:

    def __init__(self, page, ui_helper, elements: Dict[str, Any]):
        self.has_error = None
        self.page = page
        self.ui_helper = ui_helper
        self.elements = elements or {}
        self.start_time = None
        self.step_has_error = False  # 步骤错误状态
        self._log_buffer = StringIO()  # 步骤日志缓存
        self._buffer_handler_id = None
        self._prepare_evidence_dir()
        self._VALID_ACTIONS = {
            a.lower()
            for attr in dir(StepAction)
            if isinstance((alist := getattr(StepAction, attr)), list)
            for a in alist
        }

        self._NO_SELECTOR_ACTIONS = {a.lower() for a in StepAction.NO_SELECTOR_ACTIONS}

        # 初始化变量管理器
        self.variable_manager = VariableManager()

        # 初始化项目名称
        self.project_name = None

        # 已加载的模块缓存
        self.modules_cache = {}

    @staticmethod
    def _prepare_evidence_dir():
        """创建截图存储目录"""
        Path("./evidence/screenshots").mkdir(parents=True, exist_ok=True)

    def setup(self, elements: Dict[str, Any] = None):
        """设置元素定义，在测试开始前调用"""
        if elements:
            self.elements = elements

    def execute_steps(
        self, steps: List[Dict[str, Any]], project_name: str = None
    ) -> None:
        """
        执行多个测试步骤

        Args:
            steps: 测试步骤列表
            project_name: 项目名称，用于加载模块
        """
        self.project_name = project_name
        for step in steps:
            try:
                self.execute_step(step)
            except Exception as e:
                logger.error(f"步骤执行失败: {e}")
                if step.get("continue_on_failure", False):
                    logger.warning("忽略错误并继续执行")
                    continue
                raise

    def execute_step(self, step: Dict[str, Any]) -> None:
        try:
            self.start_time = datetime.now()

            # 检查是否为流程控制步骤
            if "use_module" in step:
                execute_module(self, step)
                return
            elif "if" in step:
                execute_condition(self, step)
                return
            elif "for_each" in step:
                execute_loop(self, step)
                return

            action = step.get("action", "").lower()
            pre_selector = step.get("selector")
            selector = self.variable_manager.replace_variables_refactored(
                self.elements.get(pre_selector, pre_selector)
            )  # 替换变量
            value = self.variable_manager.replace_variables_refactored(
                step.get("value")
            )  # 替换变量
            logger.debug(f"执行步骤: {action} | 选择器: {selector} | 值: {value}")
            self._validate_step(action, selector)
            self._execute_action(action, selector, value, step)

        except Exception:
            self.has_error = True
            self._capture_failure_evidence()
            raise
        finally:
            self._log_step_duration()

    def _validate_step(self, action, selector) -> None:
        if not action:
            raise ValueError("步骤缺少必要参数: action", f"原始输入: {action}")
        # 操作类型白名单校验
        if action not in self._VALID_ACTIONS:
            raise ValueError(f"不支持的操作类型: {action}")
        # 必要参数校验
        if action not in self._NO_SELECTOR_ACTIONS and not selector:
            raise ValueError(f"操作 {action} 需要提供selector参数")

    def _execute_action(
        self, action: str, selector: str, value: Any = None, step: Dict[str, Any] = None
    ) -> None:
        """执行具体操作，使用命令模式"""
        try:
            # 使用命令模式执行操作
            execute_action_with_command(self.ui_helper, action, selector, value, step)
        except Exception as e:
            logger.error(f"使用命令模式执行操作失败: {e}")
            # 如果命令模式执行失败，回退到原始实现
            self._execute_action_legacy(action, selector, value, step)

    def _execute_action_legacy(
        self, action: str, selector: str, value: Any = None, step: Dict[str, Any] = None
    ) -> None:
        """原始的操作执行方法，作为命令模式的后备"""
        action = action.lower()
        # with allure.step(f"执行步骤: {action}"):
        if action in StepAction.NAVIGATE:
            from page_objects.base_page import base_url

            url = base_url()
            if not value:
                value = url
            if "http" not in value:
                value = url + value
            self.ui_helper.navigate(value)

        elif action in StepAction.PAUSE:
            self.ui_helper.pause()

        elif action in StepAction.CLICK:
            self.ui_helper.click(selector)

        elif action in StepAction.FILL:
            self.ui_helper.fill(selector, value)

        elif action in StepAction.PRESS_KEY:
            self.ui_helper.press_key(selector, step.get("key", value))

        elif action in StepAction.UPLOAD:
            self.ui_helper.upload_file(selector, value)

        elif action in StepAction.WAIT:
            wait_time = (
                int(float(step.get("value", 1)) * 1000) if step.get("value") else 1000
            )
            self.ui_helper.wait_for_timeout(wait_time)

        elif action in StepAction.WAIT_FOR_NETWORK_IDLE:
            timeout = int(step.get("timeout", DEFAULT_TIMEOUT))
            self.ui_helper.wait_for_network_idle(timeout)

        elif action in StepAction.WAIT_FOR_ELEMENT_HIDDEN:
            timeout = int(step.get("timeout", DEFAULT_TIMEOUT))
            self.ui_helper.wait_for_element_hidden(selector, timeout)

        elif action in StepAction.WAIT_FOR_ELEMENT_CLICKABLE:
            timeout = int(step.get("timeout", DEFAULT_TIMEOUT))
            self.ui_helper.wait_for_element_clickable(selector, timeout)

        elif action in StepAction.WAIT_FOR_ELEMENT_TEXT:
            timeout = int(step.get("timeout", DEFAULT_TIMEOUT))
            expected_text = step.get("expected_text", value)
            self.ui_helper.wait_for_element_text(selector, expected_text, timeout)

        elif action in StepAction.WAIT_FOR_ELEMENT_COUNT:
            timeout = int(step.get("timeout", DEFAULT_TIMEOUT))
            expected_count = int(step.get("expected_count", value))
            self.ui_helper.wait_for_element_count(selector, expected_count, timeout)

        elif action in StepAction.ASSERT_VISIBLE:
            self.ui_helper.assert_visible(selector)

        elif action in StepAction.ASSERT_TEXT:
            expected = step.get("expected", value)
            self.ui_helper.assert_text(selector, expected)

        elif action in StepAction.HARD_ASSERT_TEXT:
            expected = step.get("expected", value)
            self.ui_helper.hard_assert_text(selector, expected)

        elif action in StepAction.ASSERT_TEXT_CONTAINS:
            expected = step.get("expected", value)
            self.ui_helper.assert_text_contains(selector, expected)

        elif action in StepAction.ASSERT_URL:
            expected = step.get("expected", value)
            self.ui_helper.assert_url(expected)

        elif action in StepAction.ASSERT_URL_CONTAINS:
            expected = step.get("expected", value)
            self.ui_helper.assert_url_contains(expected)

        elif action in StepAction.ASSERT_TITLE:
            expected = step.get("expected", value)
            self.ui_helper.assert_title(expected)

        elif action in StepAction.ASSERT_ELEMENT_COUNT:
            expected = step.get("expected", value)
            self.ui_helper.assert_element_count(selector, expected)

        elif action in StepAction.ASSERT_EXISTS:
            self.ui_helper.assert_exists(selector)

        elif action in StepAction.ASSERT_NOT_EXISTS:
            self.ui_helper.assert_not_exists(selector)

        elif action in StepAction.ASSERT_ENABLED:
            self.ui_helper.assert_element_enabled(selector)

        elif action in StepAction.ASSERT_DISABLED:
            self.ui_helper.assert_element_disabled(selector)

        elif action in StepAction.ASSERT_ATTRIBUTE:
            attribute = step.get("attribute")
            expected = step.get("expected", value)
            self.ui_helper.assert_attribute(selector, attribute, expected)

        elif action in StepAction.ASSERT_VALUE:
            expected = step.get("expected", value)
            self.ui_helper.assert_value(selector, expected)

        elif action in StepAction.STORE_VARIABLE:
            var_name = step.get("name", "temp_var")
            var_value = step.get("value")
            scope = step.get("scope", "global")
            # 存储变量
            self.variable_manager.set_variable(var_name, var_value, scope)
            logger.info(f"已存储变量 {var_name}={var_value} (scope={scope})")

        elif action in StepAction.STORE_TEXT:
            var_name = step.get("variable_name", "text_var")
            scope = step.get("scope", "global")
            # 获取元素文本
            text = self.ui_helper.get_text(selector)
            # 存储文本
            self.variable_manager.set_variable(var_name, text, scope)
            logger.info(f"已存储元素文本 {var_name}={text} (scope={scope})")

        elif action in StepAction.REFRESH:
            self.ui_helper.refresh()

        elif action in StepAction.HOVER:
            self.ui_helper.hover(selector)

        elif action in StepAction.DOUBLE_CLICK:
            self.ui_helper.double_click(selector)

        elif action in StepAction.RIGHT_CLICK:
            self.ui_helper.right_click(selector)

        elif action in StepAction.SELECT:
            self.ui_helper.select_option(selector, value)

        elif action in StepAction.DRAG_AND_DROP:
            target = step.get("target")
            self.ui_helper.drag_and_drop(selector, target)

        elif action in StepAction.GET_VALUE:
            result = self.ui_helper.get_value(selector)
            if "variable_name" in step:
                self.ui_helper.store_variable(
                    step["variable_name"], result, step.get("scope", "global")
                )

        elif action in StepAction.GET_ALL_ELEMENTS:
            elements = self.ui_helper.get_all_elements(selector)
            if "variable_name" in step:
                self.ui_helper.store_variable(
                    step["variable_name"], elements, step.get("scope", "global")
                )

        elif action in StepAction.SCROLL_INTO_VIEW:
            self.ui_helper.scroll_into_view(selector)

        elif action in StepAction.SCROLL_TO:
            x = int(step.get("x", 0))
            y = int(step.get("y", 0))
            self.ui_helper.scroll_to(x, y)

        elif action in StepAction.FOCUS:
            self.ui_helper.focus(selector)

        elif action in StepAction.BLUR:
            self.ui_helper.blur(selector)

        elif action in StepAction.TYPE:
            delay = int(step.get("delay", DEFAULT_TYPE_DELAY))
            self.ui_helper.type(selector, value, delay)

        elif action in StepAction.CLEAR:
            self.ui_helper.clear(selector)

        elif action in StepAction.ENTER_FRAME:
            self.ui_helper.enter_frame(selector)

        elif action in StepAction.ACCEPT_ALERT:
            text = self.ui_helper.accept_alert(selector, value)

        elif action in StepAction.DISMISS_ALERT:
            self.ui_helper.dismiss_alert(selector)

        elif action in StepAction.EXPECT_POPUP:
            action = step.get("real_action", "click")
            variable_name = step.get("variable_name", value)
            self.ui_helper.expect_popup(action, selector, variable_name)

        elif action in StepAction.SWITCH_WINDOW:
            self.ui_helper.switch_window(value)

        elif action in StepAction.CLOSE_WINDOW:
            self.ui_helper.close_window()

        elif action in StepAction.WAIT_FOR_NEW_WINDOW:
            new_page = self.ui_helper.wait_for_new_window()
            if "variable_name" in step:
                self.ui_helper.store_variable(
                    step["variable_name"], new_page, step.get("scope", "global")
                )

        elif action in StepAction.SAVE_ELEMENT_COUNT:
            count = self.ui_helper.get_element_count(selector)
            if "variable_name" in step:
                self.ui_helper.store_variable(
                    step["variable_name"], str(count), step.get("scope", "global")
                )

        elif action in StepAction.DOWNLOAD_FILE:
            save_path = step.get("save_path")
            file_path = self.ui_helper.download_file(selector, save_path)
            if "variable_name" in step:
                self.ui_helper.store_variable(
                    step["variable_name"], file_path, step.get("scope", "global")
                )

        elif action in StepAction.DOWNLOAD_VERIFY:
            file_pattern = step.get("file_pattern", value)
            timeout = int(step.get("timeout", DEFAULT_TIMEOUT))
            result = self.ui_helper.verify_download(file_pattern, timeout)
            if "variable_name" in step:
                self.ui_helper.store_variable(
                    step["variable_name"], str(result), step.get("scope", "global")
                )

        elif action in StepAction.FAKER:
            data_type = step.get("data_type")
            kwargs = {
                k: v
                for k, v in step.items()
                if k not in ["action", "data_type", "variable_name", "scope"]
            }

            if "variable_name" not in step:
                raise ValueError("步骤缺少必要参数: variable_name")

            # 直接使用ui_helper的方法
            value = generate_faker_data(data_type, **kwargs)
            self.ui_helper.store_variable(
                step["variable_name"], value, step.get("scope", "global")
            )

        elif action in StepAction.KEYBOARD_SHORTCUT:
            key_combination = step.get("key_combination", value)
            self.ui_helper.press_keyboard_shortcut(key_combination)

        elif action in StepAction.KEYBOARD_PRESS:
            key = step.get("key", value)
            self.ui_helper.keyboard_press(key)

        elif action in StepAction.KEYBOARD_TYPE:
            text = step.get("text", value)
            delay = int(step.get("delay", DEFAULT_TYPE_DELAY))
            self.ui_helper.keyboard_type(text, delay)
        elif action in StepAction.EXECUTE_PYTHON:
            run_dynamic_script_from_path(value)

        # 监测请求
        elif action in StepAction.MONITOR_REQUEST:
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
            # 调用监测方法
            request_data = monitor_action_request(
                self,
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
                self.variable_manager.set_variable(variable_name, request_data, scope)
                logger.info(f"已存储请求数据到变量 {variable_name}")

        # 监测响应
        elif action in StepAction.MONITOR_RESPONSE:
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

            # 调用监测方法
            response_data = monitor_action_response(
                self,
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
                self.variable_manager.set_variable(variable_name, response_data, scope)
                logger.info(f"已存储响应数据到变量 {variable_name}")

        # 保留 ASSERT_HAVE_VALUES，因为它是独特的功能
        elif action in StepAction.ASSERT_HAVE_VALUES:
            expected_values = step.get("expected_values", value)
            if isinstance(expected_values, str):
                # 尝试解析为JSON数组
                try:
                    import json

                    expected_values = json.loads(expected_values)
                except Exception:
                    # 如果不是JSON，则分割字符串
                    expected_values = expected_values.split(",")
            self.ui_helper.assert_values(selector, expected_values)

    def _replace_variables(self, value: Any) -> Any:
        """
        替换值中的变量引用

        Args:
            value: 原始值，可能包含变量引用 ${var_name} 或 $<var_name>

        Returns:
            替换后的值
        """
        if value is None:
            return value

        if isinstance(value, (int, float, bool)):
            return value

        if isinstance(value, str):
            # 处理完整的变量引用，如 ${var_name} 或 $<var_name>
            if (
                value.startswith("${")
                and value.endswith("}")
                and value.count("${") == 1
            ) or (
                value.startswith("$<")
                and value.endswith(">")
                and value.count("$<") == 1
            ):

                if value.startswith("${"):
                    var_name = value[2:-1]
                else:  # value.startswith("$<")
                    var_name = value[2:-1]

                return self.variable_manager.get_variable(var_name)

            # 替换内嵌变量引用
            import re

            # 同时匹配 ${var_name} 和 $<var_name> 两种模式
            pattern = r"\${([^{}]+)}|\$<([^<>]+)>"

            def replace_var(match):
                # 获取匹配的组，第一个组是 ${} 形式，第二个组是 $<> 形式
                var_name = (
                    match.group(1) if match.group(1) is not None else match.group(2)
                )
                var_value = self.variable_manager.get_variable(var_name)
                return str(var_value) if var_value is not None else match.group(0)

            # 使用正则表达式替换所有变量引用
            result = re.sub(pattern, replace_var, value)
            return result

        if isinstance(value, list):
            return [self._replace_variables(item) for item in value]

        if isinstance(value, dict):
            return {k: self._replace_variables(v) for k, v in value.items()}

        return value

    def _evaluate_expression(self, expression: str) -> bool:
        """
        计算表达式的值

        Args:
            expression: 表达式字符串，如 "${{ ${count} > 5 }}"

        Returns:
            表达式的布尔结果
        """
        return evaluate_expression(self, expression)

    def _finalize_step(self):
        """统一后处理逻辑"""
        # 移除日志handler
        if self._buffer_handler_id:
            logger.remove(self._buffer_handler_id)
            self._buffer_handler_id = None

        # 记录耗时
        self._log_step_duration()

        # 失败时采集证据
        if self.step_has_error:
            self._capture_failure_evidence()

    def _log_step_duration(self):
        """统一记录步骤耗时"""
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            status = "成功" if not self.step_has_error else "失败"
            logger.debug(f"[{status}] 步骤耗时: {duration:.2f}s")

    def _capture_failure_evidence(self):
        """统一失败证据采集"""
        try:
            # 生成时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 3. 捕获步骤日志
            log_content = self._log_buffer.getvalue()
            allure.attach(
                log_content,
                name="步骤日志",
                attachment_type=allure.attachment_type.TEXT,
            )

            # 4. 记录上下文信息
            context_info = f"URL: {self.page.url}\n错误时间: {timestamp}"
            allure.attach(
                context_info,
                name="失败上下文",
                attachment_type=allure.attachment_type.TEXT,
            )

        except Exception as e:
            logger.error(f"证据采集失败: {str(e)}")
