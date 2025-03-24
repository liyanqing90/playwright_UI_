from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Dict, Any

import allure

from constants import DEFAULT_TYPE_DELAY, DEFAULT_TIMEOUT
from page_objects.base_page import base_url
from utils.logger import logger
from utils.variable_manager import VariableManager


class StepAction:
    """操作类型定义"""
    # 基础操作
    NAVIGATE = ['navigate', 'goto', '打开', '访问']
    CLICK = ['click', '点击']
    FILL = ['fill', '输入']
    PRESS_KEY = ['press_key', '按键']
    WAIT = ['wait', '等待']

    #执行Python文件
    EXECUTE_PYTHON = ['execute_python', '执行Python']
    # 断言相关
    ASSERT_VISIBLE = ['assert_visible', '验证可见']
    ASSERT_TEXT = ['assert_text', 'assertion', '验证文本', "验证", 'verify']
    ASSERT_ATTRIBUTE = ['assert_attribute', '验证属性']
    ASSERT_URL = ['assert_url', '验证URL']
    ASSERT_TITLE = ['assert_title', '验证标题']
    ASSERT_ELEMENT_COUNT = ['assert_element_count', '验证元素数量']
    ASSERT_TEXT_CONTAINS = ['assert_text_contains', '验证包含文本']
    ASSERT_URL_CONTAINS = ['assert_url_contains', '验证URL包含']
    ASSERT_EXISTS = ['assert_exists', '验证存在']
    ASSERT_NOT_EXISTS = ['assert_not_exists', '验证不存在']
    ASSERT_ENABLED = ['assert_enabled', '验证启用']
    ASSERT_DISABLED = ['assert_disabled', '验证禁用']
    ASSERT_VALUE = ['assert_value', '验证值']

    # 存储相关
    STORE_VARIABLE = ['store_variable', '存储变量']
    STORE_TEXT = ['store_text', '存储文本']
    STORE_ATTRIBUTE = ['store_attribute', '存储属性']

    # 等待相关
    WAIT_FOR_ELEMENT_HIDDEN = ['wait_for_element_hidden', '等待元素消失']
    WAIT_FOR_NETWORK_IDLE = ['wait_for_network_idle', '等待网络空闲']
    WAIT_FOR_ELEMENT_CLICKABLE = ['wait_for_element_clickable', '等待元素可点击']
    WAIT_FOR_ELEMENT_TEXT = ['wait_for_element_text', '等待元素文本']
    WAIT_FOR_ELEMENT_COUNT = ['wait_for_element_count', '等待元素数量']

    # 其他操作
    REFRESH = ['refresh', '刷新']
    PAUSE = ['pause', '暂停']
    UPLOAD = ['upload', '上传', '上传文件']
    HOVER = ['hover', '悬停']
    DOUBLE_CLICK = ['double_click', '双击']
    RIGHT_CLICK = ['right_click', '右键点击']
    SELECT = ['select', '选择']
    DRAG_AND_DROP = ['drag_and_drop', '拖拽']
    GET_VALUE = ['get_value', '获取值']
    SCROLL_INTO_VIEW = ['scroll_into_view', '滚动到元素']
    SCROLL_TO = ['scroll_to', '滚动到位置']
    FOCUS = ['focus', '聚焦']
    BLUR = ['blur', '失焦']
    TYPE = ['type', '模拟输入']
    CLEAR = ['clear', '清空']
    ENTER_FRAME = ['enter_frame', '进入框架']
    ACCEPT_ALERT = ['accept_alert', '接受弹框']
    DISMISS_ALERT = ['dismiss_alert', '取消弹框']
    EXPECT_POPUP = ['expect_popup', '弹出tab']
    SWITCH_WINDOW = ['switch_window', '切换窗口']
    CLOSE_WINDOW = ['close_window', '关闭窗口']
    WAIT_FOR_NEW_WINDOW = ['wait_for_new_window', '等待新窗口']
    SAVE_ELEMENT_COUNT = ['save_ele_count', '存储元素数量']
    EXECUTE_SCRIPT = ['execute_script', '执行脚本']
    CAPTURE_SCREENSHOT = ['capture', '截图']
    MANAGE_COOKIES = ['cookies', 'Cookie操作']
    TAB_SWITCH = ['switch_tab', '切换标签页']
    DOWNLOAD_FILE = ['download', '下载文件']
    DOWNLOAD_VERIFY = ['verify_download', '验证下载']
    FAKER = ['faker', '生成数据']
    GET_ALL_ELEMENTS = ['get_all_elements', '获取所有元素']
    KEYBOARD_SHORTCUT = ['keyboard_shortcut', '键盘快捷键']
    KEYBOARD_PRESS = ['keyboard_press', '全局按键']
    KEYBOARD_TYPE = ['keyboard_type', '全局输入']
    # 不需要selector的操作
    NO_SELECTOR_ACTIONS = (
            NAVIGATE +
            ASSERT_URL +
            ASSERT_TITLE +
            ASSERT_URL_CONTAINS +
            EXECUTE_PYTHON +
            WAIT +
            WAIT_FOR_NETWORK_IDLE +
            REFRESH +
            PAUSE +
            CLOSE_WINDOW +
            WAIT_FOR_NEW_WINDOW +
            SAVE_ELEMENT_COUNT +
            EXECUTE_SCRIPT +
            CAPTURE_SCREENSHOT +
            MANAGE_COOKIES +
            TAB_SWITCH +
            DOWNLOAD_VERIFY +
            FAKER +
            KEYBOARD_SHORTCUT +
            KEYBOARD_PRESS +
            KEYBOARD_TYPE
    )


class StepExecutor:

    def __init__(self, page, ui_helper, elements: Dict[str, Any]):
        self.has_error = None
        self.page = page
        self.ui_helper = ui_helper
        self.elements = elements
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

        self._NO_SELECTOR_ACTIONS = {
            a.lower() for a in StepAction.NO_SELECTOR_ACTIONS
        }

    @staticmethod
    def _prepare_evidence_dir():
        """创建截图存储目录"""
        Path("./evidence/screenshots").mkdir(parents=True, exist_ok=True)
        # 日志handler ID        Path("./evidence/screenshots").mkdir(parents=True, exist_ok=True)

    def execute_step(self, step: Dict[str, Any]) -> None:
        try:

            self.start_time = datetime.now()

            action = step.get("action", "").lower()
            pre_selector = step.get("selector")
            selector = self.elements.get(pre_selector, pre_selector)  # 替换变量
            value = replace_values_from_dict_regex(step.get("value"))  # 替换变量
            logger.debug(f"执行步骤: {action} | 选择器: {pre_selector} | 值: {value}")
            self._validate_step(action, selector)
            self._execute_action(action, selector, value, step)

        except Exception as e:
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
        if (action not in self._NO_SELECTOR_ACTIONS and
                not selector):
            raise ValueError(f"操作 {action} 需要提供selector参数")

    def _execute_action(self, action: str, selector: str, value: Any = None, step: Dict[str, Any] = None) -> None:
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
            self.ui_helper.press_key(selector, step.get('key', value))

        elif action in StepAction.UPLOAD:
            self.ui_helper.upload_file(selector, value)

        elif action in StepAction.WAIT:
            wait_time = int(float(step.get('value', 1)) * 1000) if step.get('value') else 1000
            self.ui_helper.wait_for_timeout(wait_time)

        elif action in StepAction.WAIT_FOR_NETWORK_IDLE:
            timeout = int(step.get('timeout', DEFAULT_TIMEOUT))
            self.ui_helper.wait_for_network_idle(timeout)

        elif action in StepAction.WAIT_FOR_ELEMENT_HIDDEN:
            timeout = int(step.get('timeout', DEFAULT_TIMEOUT))
            self.ui_helper.wait_for_element_hidden(selector, timeout)

        elif action in StepAction.WAIT_FOR_ELEMENT_CLICKABLE:
            timeout = int(step.get('timeout', DEFAULT_TIMEOUT))
            self.ui_helper.wait_for_element_clickable(selector, timeout)

        elif action in StepAction.WAIT_FOR_ELEMENT_TEXT:
            timeout = int(step.get('timeout', DEFAULT_TIMEOUT))
            expected_text = step.get('expected_text', value)
            self.ui_helper.wait_for_element_text(selector, expected_text, timeout)

        elif action in StepAction.WAIT_FOR_ELEMENT_COUNT:
            timeout = int(step.get('timeout', DEFAULT_TIMEOUT))
            expected_count = int(step.get('expected_count', value))
            self.ui_helper.wait_for_element_count(selector, expected_count, timeout)

        elif action in StepAction.ASSERT_VISIBLE:
            self.ui_helper.assert_visible(selector)

        elif action in StepAction.ASSERT_TEXT:
            expected = step.get('expected', value)
            self.ui_helper.assert_text(selector, expected)

        elif action in StepAction.ASSERT_TEXT_CONTAINS:
            expected = step.get('expected', value)
            self.ui_helper.assert_text_contains(selector, expected)

        elif action in StepAction.ASSERT_URL:
            expected = step.get('expected', value)
            self.ui_helper.assert_url(expected)

        elif action in StepAction.ASSERT_URL_CONTAINS:
            expected = step.get('expected', value)
            self.ui_helper.assert_url_contains(expected)

        elif action in StepAction.ASSERT_TITLE:
            expected = step.get('expected', value)
            self.ui_helper.assert_title(expected)

        elif action in StepAction.ASSERT_ELEMENT_COUNT:
            expected = step.get('expected', value)
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
            attribute = step.get('attribute')
            expected = step.get('expected', value)
            self.ui_helper.assert_attribute(selector, attribute, expected)

        elif action in StepAction.ASSERT_VALUE:
            expected = step.get('expected', value)
            self.ui_helper.assert_value(selector, expected)

        elif action in StepAction.STORE_VARIABLE:
            self.ui_helper.store_variable(step['name'], value, step.get('scope', 'global'))

        elif action in StepAction.STORE_TEXT:
            self.ui_helper.store_text(selector, step.get('variable_name', value), step.get('scope', 'global'))

        elif action in StepAction.STORE_ATTRIBUTE:
            self.ui_helper.store_attribute(
                selector,
                step['attribute'],
                step.get('variable_name', value),
                step.get('scope', 'global')
            )

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
            target = step.get('target')
            self.ui_helper.drag_and_drop(selector, target)

        elif action in StepAction.GET_VALUE:
            result = self.ui_helper.get_value(selector)
            if 'variable_name' in step:
                self.ui_helper.store_variable(step['variable_name'], result, step.get('scope', 'global'))

        elif action in StepAction.GET_ALL_ELEMENTS:
            elements = self.ui_helper.get_all_elements(selector)
            if 'variable_name' in step:
                self.ui_helper.store_variable(step['variable_name'], elements, step.get('scope', 'global'))

        elif action in StepAction.SCROLL_INTO_VIEW:
            self.ui_helper.scroll_into_view(selector)

        elif action in StepAction.SCROLL_TO:
            x = int(step.get('x', 0))
            y = int(step.get('y', 0))
            self.ui_helper.scroll_to(x, y)

        elif action in StepAction.FOCUS:
            self.ui_helper.focus(selector)

        elif action in StepAction.BLUR:
            self.ui_helper.blur(selector)

        elif action in StepAction.TYPE:
            delay = int(step.get('delay', 100))
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
            variable_name = step.get('variable_name', value)
            self.ui_helper.expect_popup(action, selector,variable_name)

        elif action in StepAction.SWITCH_WINDOW:
            self.ui_helper.switch_window(value)

        elif action in StepAction.CLOSE_WINDOW:
            self.ui_helper.close_window()

        elif action in StepAction.WAIT_FOR_NEW_WINDOW:
            new_page = self.ui_helper.wait_for_new_window()
            if 'variable_name' in step:
                self.ui_helper.store_variable(step['variable_name'], new_page, step.get('scope', 'global'))

        elif action in StepAction.SAVE_ELEMENT_COUNT:
            count = self.ui_helper.get_element_count(selector)
            if 'variable_name' in step:
                self.ui_helper.store_variable(step['variable_name'], str(count), step.get('scope', 'global'))

        elif action in StepAction.DOWNLOAD_FILE:
            save_path = step.get('save_path')
            file_path = self.ui_helper.download_file(selector, save_path)
            if 'variable_name' in step:
                self.ui_helper.store_variable(step['variable_name'], file_path, step.get('scope', 'global'))

        elif action in StepAction.DOWNLOAD_VERIFY:
            file_pattern = step.get('file_pattern', value)
            timeout = int(step.get('timeout', DEFAULT_TIMEOUT))
            result = self.ui_helper.verify_download(file_pattern, timeout)
            if 'variable_name' in step:
                self.ui_helper.store_variable(step['variable_name'], str(result), step.get('scope', 'global'))

        elif action in StepAction.FAKER:
            data_type = step.get('data_type')
            kwargs = {k: v for k, v in step.items() if k not in ['action', 'data_type', 'variable_name', 'scope']}

            if 'variable_name' not in step:
                raise ValueError("步骤缺少必要参数: variable_name")

            # 直接使用ui_helper的方法
            value = self.ui_helper.generate_faker_data(data_type, **kwargs)
            self.ui_helper.store_variable(step['variable_name'], value, step.get('scope', 'global'))

        elif action in StepAction.KEYBOARD_SHORTCUT:
            key_combination = step.get('key_combination', value)
            self.ui_helper.press_keyboard_shortcut(key_combination)

        elif action in StepAction.KEYBOARD_PRESS:
            key = step.get('key', value)
            self.ui_helper.keyboard_press(key)

        elif action in StepAction.KEYBOARD_TYPE:
            text = step.get('text', value)
            delay = int(step.get('delay', DEFAULT_TYPE_DELAY))
            self.ui_helper.keyboard_type(text, delay)
        elif action in StepAction.EXECUTE_PYTHON:
            run_dynamic_script_from_path(value)

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
                attachment_type=allure.attachment_type.TEXT
            )

            # 4. 记录上下文信息
            context_info = f"URL: {self.page.url}\n错误时间: {timestamp}"
            allure.attach(
                context_info,
                name="失败上下文",
                attachment_type=allure.attachment_type.TEXT
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
    if data_type == 'name':
        faker = Faker()
        return "新零售" + faker.uuid4().replace("-", "")[:6]
    elif data_type == 'mobile':
        return '18210233933'
    else:
        raise "不支持的类型"


import re


def replace_values_from_dict_regex(value_string):
    """
    使用正则表达式从字典中替换字符串中的占位符。

    Args:
      value_string: 包含占位符的字符串，占位符格式为 '$<key>'。

    Returns:
      替换占位符后的字符串。
    """
    if not value_string or "$<" not in str(value_string): return value_string
    variable_manager = VariableManager()

    def replace_placeholder(match):
        """正则表达式替换的回调函数，用于获取匹配到的占位符键名并替换。"""
        placeholder_key = match.group(1)  # 获取捕获组 (括号内的内容)，即占位符的键名
        value = variable_manager.get_variable(placeholder_key)  # 使用字典的 get() 方法安全地获取值
        if value is not None:
            return str(value)  # 如果找到值，则替换为字典中的值
        else:
            print(f"Warning: Key '{placeholder_key}' not found in the dictionary. Placeholder will be kept.")
            return match.group(0)  # 如果键未找到，打印警告信息并保留原始占位符

    pattern = r"\$\<(\w+)\>"
    replaced_string = re.sub(pattern, replace_placeholder, value_string)
    return replaced_string
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
        spec = importlib.util.spec_from_file_location(module_name, str(file_path))  # 创建模块规范, 需要字符串路径
        if spec is None:
            print(f"无法从文件路径 {file_path} 创建模块规范。")
            return
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        # 检查模块是否定义了一个 `run()` 函数，如果有，则调用它
        if hasattr(module, 'run'):
            module.run()
        elif hasattr(module, 'main'):
            module.main()
        else:
            print(f"模块 {module_name} 没有 'run' 或 'main' 函数。")
    except FileNotFoundError as e:
        print(e)  # 直接打印 FileNotFoundError 异常信息
    except Exception as e:
        print(f"导入或执行模块 {file_path} 时发生错误：{e}")

