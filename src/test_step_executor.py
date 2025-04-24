import json
import os
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Dict, Any, List
from utils.variable_manager import VariableManager

import allure

from constants import DEFAULT_TYPE_DELAY, DEFAULT_TIMEOUT
from page_objects.base_page import base_url
from utils.logger import logger


class StepAction:
    """操作类型定义"""

    # 基础操作
    NAVIGATE = ["navigate", "goto", "打开", "访问"]
    CLICK = ["click", "点击"]
    FILL = ["fill", "输入"]
    PRESS_KEY = ["press_key", "按键"]
    WAIT = ["wait", "等待"]

    # 执行Python文件
    EXECUTE_PYTHON = ["execute_python", "执行Python"]
    # 断言相关
    HARD_ASSERT_TEXT = ["hard_assert", "硬断言"]
    ASSERT_VISIBLE = ["assert_visible", "验证可见"]
    ASSERT_TEXT = ["assert_text", "assertion", "验证文本", "验证", "verify"]
    ASSERT_ATTRIBUTE = ["assert_attribute", "验证属性"]
    ASSERT_URL = ["assert_url", "验证URL"]
    ASSERT_TITLE = ["assert_title", "验证标题"]
    ASSERT_ELEMENT_COUNT = ["assert_element_count", "验证元素数量"]
    ASSERT_TEXT_CONTAINS = ["assert_text_contains", "验证包含文本"]
    ASSERT_URL_CONTAINS = ["assert_url_contains", "验证URL包含"]
    ASSERT_EXISTS = ["assert_exists", "验证存在"]
    ASSERT_NOT_EXISTS = ["assert_not_exists", "验证不存在"]
    ASSERT_ENABLED = ["assert_enabled", "验证启用"]
    ASSERT_DISABLED = ["assert_disabled", "验证禁用"]
    ASSERT_VALUE = ["assert_value", "验证值"]

    ASSERT_HAVE_VALUES = ["assert_have_values", "验证多个值"]

    # 存储相关
    STORE_VARIABLE = ["store_variable", "存储变量"]
    STORE_TEXT = ["store_text", "存储文本"]
    STORE_ATTRIBUTE = ["store_attribute", "存储属性"]

    # 等待相关
    WAIT_FOR_ELEMENT_HIDDEN = ["wait_for_element_hidden", "等待元素消失"]
    WAIT_FOR_NETWORK_IDLE = ["wait_for_network_idle", "等待网络空闲"]
    WAIT_FOR_ELEMENT_CLICKABLE = ["wait_for_element_clickable", "等待元素可点击"]
    WAIT_FOR_ELEMENT_TEXT = ["wait_for_element_text", "等待元素文本"]
    WAIT_FOR_ELEMENT_COUNT = ["wait_for_element_count", "等待元素数量"]

    # 其他操作
    REFRESH = ["refresh", "刷新"]
    PAUSE = ["pause", "暂停"]
    UPLOAD = ["upload", "上传", "上传文件"]
    HOVER = ["hover", "悬停"]
    DOUBLE_CLICK = ["double_click", "双击"]
    RIGHT_CLICK = ["right_click", "右键点击"]
    SELECT = ["select", "选择"]
    DRAG_AND_DROP = ["drag_and_drop", "拖拽"]
    GET_VALUE = ["get_value", "获取值"]
    SCROLL_INTO_VIEW = ["scroll_into_view", "滚动到元素"]
    SCROLL_TO = ["scroll_to", "滚动到位置"]
    FOCUS = ["focus", "聚焦"]
    BLUR = ["blur", "失焦"]
    TYPE = ["type", "模拟输入"]
    CLEAR = ["clear", "清空"]
    ENTER_FRAME = ["enter_frame", "进入框架"]
    ACCEPT_ALERT = ["accept_alert", "接受弹框"]
    DISMISS_ALERT = ["dismiss_alert", "取消弹框"]
    EXPECT_POPUP = ["expect_popup", "弹出tab"]
    SWITCH_WINDOW = ["switch_window", "切换窗口"]
    CLOSE_WINDOW = ["close_window", "关闭窗口"]
    WAIT_FOR_NEW_WINDOW = ["wait_for_new_window", "等待新窗口"]
    SAVE_ELEMENT_COUNT = ["save_ele_count", "存储元素数量"]
    EXECUTE_SCRIPT = ["execute_script", "执行脚本"]
    CAPTURE_SCREENSHOT = ["capture", "截图"]
    MANAGE_COOKIES = ["cookies", "Cookie操作"]
    TAB_SWITCH = ["switch_tab", "切换标签页"]
    DOWNLOAD_FILE = ["download", "下载文件"]
    DOWNLOAD_VERIFY = ["verify_download", "验证下载"]
    FAKER = ["faker", "生成数据"]
    GET_ALL_ELEMENTS = ["get_all_elements", "获取所有元素"]
    KEYBOARD_SHORTCUT = ["keyboard_shortcut", "键盘快捷键"]
    KEYBOARD_PRESS = ["keyboard_press", "全局按键"]
    KEYBOARD_TYPE = ["keyboard_type", "全局输入"]

    # 流程控制操作
    USE_MODULE = ["use_module", "使用模块"]
    IF_CONDITION = ["if", "如果"]
    FOR_EACH = ["for_each", "循环"]

    # 接口监测相关
    MONITOR_REQUEST = ["monitor_request", "监测请求"]
    MONITOR_RESPONSE = ["monitor_response", "监测响应"]

    # 不需要selector的操作
    NO_SELECTOR_ACTIONS = (
        NAVIGATE
        + ASSERT_URL
        + ASSERT_TITLE
        + ASSERT_URL_CONTAINS
        + EXECUTE_PYTHON
        + WAIT
        + WAIT_FOR_NETWORK_IDLE
        + REFRESH
        + PAUSE
        + CLOSE_WINDOW
        + WAIT_FOR_NEW_WINDOW
        + SAVE_ELEMENT_COUNT
        + EXECUTE_SCRIPT
        + CAPTURE_SCREENSHOT
        + MANAGE_COOKIES
        + TAB_SWITCH
        + DOWNLOAD_VERIFY
        + FAKER
        + KEYBOARD_SHORTCUT
        + KEYBOARD_PRESS
        + KEYBOARD_TYPE
        + USE_MODULE
        + IF_CONDITION
        + FOR_EACH
    )


def _replace_module_params(
    steps: List[Dict[str, Any]], params: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    替换模块步骤中的参数

    Args:
        steps: 模块步骤列表
        params: 参数字典

    Returns:
        处理后的步骤列表
    """
    import copy

    processed_steps = copy.deepcopy(steps)

    def replace_in_value(value):
        if isinstance(value, str):
            # 替换参数引用，格式为 ${param_name}
            for param_name, param_value in params.items():
                placeholder = "${" + param_name + "}"
                if placeholder in value:
                    value = value.replace(placeholder, str(param_value))
        return value

    def process_step_dict(step_dict):
        for key, value in step_dict.items():
            if isinstance(value, dict):
                process_step_dict(value)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        process_step_dict(item)
                    else:
                        value[i] = replace_in_value(item)
            else:
                step_dict[key] = replace_in_value(value)

    for step in processed_steps:
        process_step_dict(step)

    return processed_steps


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
        # 日志handler ID        Path("./evidence/screenshots").mkdir(parents=True, exist_ok=True)

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
                self._execute_module(step)
                return
            elif "if" in step:
                self._execute_condition(step)
                return
            elif "for_each" in step:
                self._execute_loop(step)
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

    def _execute_module(self, step: Dict[str, Any]) -> None:
        """
        执行模块引用

        Args:
            step: 包含use_module字段的步骤
        """
        module_name = step["use_module"]
        params = step.get("params", {})
        description = step.get("description", f"执行模块 {module_name}")

        logger.info(f"开始执行模块: {module_name} {description}")

        # 处理参数中的变量
        processed_params = {}
        for key, value in params.items():
            processed_params[key] = self._replace_variables(value)

        # 加载模块步骤
        try:
            # 尝试从缓存中获取模块
            if self.modules_cache.get(module_name):
                module_data = self.modules_cache[module_name]
            else:
                # 获取模块路径和数据
                module_data = self._find_module(module_name)

                # 缓存模块数据
                self.modules_cache[module_name] = module_data

            # 获取步骤列表
            if "steps" in module_data:
                steps = module_data["steps"]
            elif module_data:
                # 获取第一个键对应的值
                first_key = next(iter(module_data))
                steps = module_data[first_key]
            else:
                raise ValueError(f"模块 '{module_name}' 中没有找到步骤")

            # 替换参数
            processed_steps = _replace_module_params(steps, processed_params)

            # 执行模块步骤
            with allure.step(f"执行模块: {module_name}"):
                for module_step in processed_steps:
                    self.execute_step(module_step)

            logger.info(f"模块 '{module_name}' 执行完成")
        except Exception as e:
            logger.error(f"执行模块 '{module_name}' 失败: {e}")
            raise

    def _find_module(self, module_name: str) -> Dict[str, Any]:
        """
        查找并加载模块数据

        Args:
            module_name: 模块名称

        Returns:
            模块数据

        Raises:
            ValueError: 如果找不到模块
        """
        from utils.yaml_handler import YamlHandler
        from pathlib import Path

        yaml_handler = YamlHandler()

        # 确定模块目录
        if self.project_name:
            modules_dir = Path("test_data") / self.project_name / "modules"
        else:
            test_dir = os.environ.get("TEST_DIR", "test_data")
            modules_dir = Path(test_dir) / "modules"

        # 如果没有找到直接匹配的文件，使用load_yaml_dir加载整个目录
        all_modules = yaml_handler.load_yaml_dir(modules_dir)

        # 检查是否有匹配的模块名
        if module_name in all_modules:
            return {module_name: all_modules[module_name]}

        # 如果所有尝试都失败，抛出错误
        raise ValueError(f"找不到模块: {module_name}")

    def _execute_condition(self, step: Dict[str, Any]) -> None:
        """
        执行条件分支

        Args:
            step: 包含if字段的步骤
        """
        condition = step["if"]
        then_steps = step.get("then", [])
        else_steps = step.get("else", [])
        description = step.get("description", "条件分支")

        # 计算条件表达式
        # 先获取原始表达式内容用于日志
        original_condition = condition

        # 提取表达式内容（如果是${{...}}格式）
        if condition.startswith("${{") and condition.endswith("}}"):
            expr_content = condition[3:-2].strip()
            # 替换变量得到可读的表达式
            readable_expr = self._replace_variables(expr_content)
        else:
            readable_expr = self._replace_variables(condition)

        # 计算条件结果
        condition_result = self._evaluate_expression(condition)

        with allure.step(
            f"条件分支: {description} ({readable_expr} = {condition_result})"
        ):
            if condition_result:
                logger.info(f"条件 '{readable_expr}' 为真，执行THEN分支")
                for then_step in then_steps:
                    self.execute_step(then_step)
            else:
                logger.info(f"条件 '{readable_expr}' 为假，执行ELSE分支")
                for else_step in else_steps:
                    self.execute_step(else_step)

    def _execute_loop(self, step: Dict[str, Any]) -> None:
        """
        执行循环

        Args:
            step: 包含for_each字段的步骤
        """
        items = step["for_each"]
        as_var = step.get("as", "item")
        do_steps = step.get("do", [])
        description = step.get("description", "循环")

        # 处理循环项，可能是变量引用或直接值
        if isinstance(items, str) and items.startswith("${") and items.endswith("}"):
            var_name = items[2:-1]
            items_value = self.variable_manager.get_variable(var_name)
        else:
            items_value = items

        # 确保循环项是可迭代的
        if not isinstance(items_value, (list, tuple, dict)):
            if isinstance(items_value, str):
                try:
                    # 尝试解析为JSON
                    items_value = json.loads(items_value)
                except json.JSONDecodeError:
                    # 如果不是JSON，则转为列表
                    items_value = [items_value]
            else:
                items_value = [items_value]

        # 如果是字典，则遍历键
        if isinstance(items_value, dict):
            items_value = list(items_value.keys())

        with allure.step(f"循环: {description} (迭代 {len(items_value)} 个项)"):
            for i, item in enumerate(items_value):
                logger.info(f"循环项 {i + 1}/{len(items_value)}: {item}")

                # 设置循环变量
                self.variable_manager.set_variable(as_var, item, "test_case")

                # 执行循环体
                for do_step in do_steps:
                    self.execute_step(do_step)

    def _evaluate_expression(self, expression: str) -> bool:
        """
        计算表达式的值

        Args:
            expression: 表达式字符串，如 "${{ ${count} > 5 }}"

        Returns:
            表达式的布尔结果
        """
        # 检查是否是表达式格式
        if not (expression.startswith("${{") and expression.endswith("}}")):
            # 不是表达式，直接返回表达式值的布尔性
            return bool(self._replace_variables(expression))

        # 提取表达式内容
        expr_content = expression[3:-2].strip()

        # 替换所有变量引用
        expr_content = self._replace_variables(expr_content)

        # 安全计算表达式
        try:
            # 为了安全起见，我们需要确保字符串值被正确引用
            # 创建一个安全的执行环境
            safe_globals = {"__builtins__": {}}

            # 尝试将表达式中的字符串值用引号括起来
            # 这是一个简单的方法，可能需要更复杂的解析来处理所有情况
            if "==" in expr_content or "!=" in expr_content:
                parts = []
                if "==" in expr_content:
                    parts = expr_content.split("==")
                    operator = "=="
                else:
                    parts = expr_content.split("!=")
                    operator = "!="

                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()

                    # 如果左右两边不是已经被引号括起来的，且不是纯数字，则添加引号
                    if not (left.startswith('"') and left.endswith('"')) and not (
                        left.startswith("'") and left.endswith("'")
                    ):
                        try:
                            float(left)  # 尝试转换为数字
                        except ValueError:
                            left = f"'{left}'"  # 不是数字，添加引号

                    if not (right.startswith('"') and right.endswith('"')) and not (
                        right.startswith("'") and right.endswith("'")
                    ):
                        try:
                            float(right)  # 尝试转换为数字
                        except ValueError:
                            right = f"'{right}'"  # 不是数字，添加引号

                    expr_content = f"{left} {operator} {right}"

            # 执行表达式
            result = eval(expr_content, safe_globals)
            return bool(result)
        except Exception as e:
            logger.error(f"表达式计算错误: {expr_content} - {e}")
            return False

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

    def _execute_action(
        self, action: str, selector: str, value: Any = None, step: Dict[str, Any] = None
    ) -> None:
        """执行具体操作"""
        action = action.lower()
        # with allure.step(f"执行步骤: {action}"):
        if action in StepAction.NAVIGATE:
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
            delay = int(step.get("delay", 100))
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
            request_data = self.ui_helper.monitor_action_request(
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
            response_data = self.ui_helper.monitor_action_response(
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
            #
            # # 1. 捕获屏幕截图
            # screenshot_path = f"./evidence/screenshots/failure_{timestamp}.png"
            # self.page.screenshot(path=screenshot_path, full_page=True)
            # allure.attach.file(
            #     screenshot_path,
            #     name="失败截图",
            #     attachment_type=allure.attachment_type.PNG
            # )
            #
            # # 2. 捕获页面HTML
            # html_content = self.page.content()
            # allure.attach(
            #     html_content,
            #     name="页面HTML",
            #     attachment_type=allure.attachment_type.HTML
            # )

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


def generate_faker_data(data_type, **kwargs):
    """
    生成Faker数据的辅助函数
    这个函数只是为了兼容旧代码，实际调用BasePage中的方法
    """
    from faker import Faker

    # 兼容旧的简单数据类型
    if data_type == "name":
        faker = Faker()
        return "新零售" + faker.uuid4().replace("-", "")[:6]
    elif data_type == "mobile":
        return "18210233933"
    else:
        raise "不支持的类型"


def run_dynamic_script_from_path(file_path: Path):
    """
    从 Path 对象表示的文件路径动态地导入和执行一个 Python 模块。
    Args:
        file_path:  A pathlib.Path object pointing to the Python file.
    """

    import importlib.util
    import sys

    file_path = Path(file_path)
    try:
        if not file_path.exists():
            raise FileNotFoundError(f"文件 {file_path} 不存在。")
        module_name = file_path.stem  # 获取不带扩展名的文件名 (模块名)
        spec = importlib.util.spec_from_file_location(
            module_name, str(file_path)
        )  # 创建模块规范, 需要字符串路径
        if spec is None:
            print(f"无法从文件路径 {file_path} 创建模块规范。")
            return
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        # 检查模块是否定义了一个 `run()` 函数，如果有，则调用它
        if hasattr(module, "run"):
            module.run()
        elif hasattr(module, "main"):
            module.main()
        else:
            print(f"模块 {module_name} 没有 'run' 或 'main' 函数。")
    except FileNotFoundError as e:
        print(e)  # 直接打印 FileNotFoundError 异常信息
    except Exception as e:
        print(f"导入或执行模块 {file_path} 时发生错误：{e}")
