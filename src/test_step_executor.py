from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import allure

from page_objects.base_page import base_url
from utils.logger import logger


class StepAction:
    """操作类型定义"""
    # 基础操作
    NAVIGATE = ['navigate', 'goto', '打开', '访问']
    CLICK = ['click', '点击']
    FILL = ['fill', '输入']
    PRESS_KEY = ['press_key', '按键']
    WAIT = ['wait', '等待']

    # 断言相关
    ASSERT_VISIBLE = ['assert_visible', '验证可见']
    ASSERT_TEXT = ['assert_text', 'assertion', '验证文本']

    # 存储相关
    STORE_VARIABLE = ['store_variable', '存储变量']
    STORE_TEXT = ['store_text', '存储文本']
    STORE_ATTRIBUTE = ['store_attribute', '存储属性']

    # 其他操作
    REFRESH = ['refresh', '刷新']
    VERIFY = ['verify', '验证']
    PAUSE = ['pause', '暂停']
    UPLOAD = ['upload', '上传文件']
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
    EXIT_FRAME = ['exit_frame', '退出框架']
    ACCEPT_ALERT = ['accept_alert', '接受弹框']
    DISMISS_ALERT = ['dismiss_alert', '取消弹框']
    SWITCH_WINDOW = ['switch_window', '切换窗口']
    CLOSE_WINDOW = ['close_window', '关闭窗口']
    WAIT_FOR_NEW_WINDOW = ['wait_for_new_window', '等待新窗口']
    GET_ELEMENT_COUNT = ['get_element_count', '获取元素数量']
    EXECUTE_SCRIPT = ['execute_script', '执行脚本']
    CAPTURE_SCREENSHOT = ['capture', '截图']
    MANAGE_COOKIES = ['cookies', 'Cookie操作']
    TAB_SWITCH = ['switch_tab', '切换标签页']
    DOWNLOAD_VERIFY = ['verify_download', '验证下载']
    # 不需要selector的操作
    NO_SELECTOR_ACTIONS = (
            NAVIGATE +
            WAIT +
            REFRESH +
            PAUSE +
            CLOSE_WINDOW +
            EXIT_FRAME +
            WAIT_FOR_NEW_WINDOW
    )


class StepExecutor:
    def __init__(self, page, ui_helper, elements: Dict[str, Any]):
        self.page = page
        self.ui_helper = ui_helper
        self.elements = elements
        self.start_time = None
        Path("./evidence/screenshots").mkdir(parents=True, exist_ok=True)

    def execute_step(self, step: Dict[str, Any]) -> None:
        try:
            self.start_time = datetime.now()
            self._validate_step(step)

            action = step.get("action")
            selector = step.get("selector")
            value = step.get("value")

            if selector and selector in self.elements:
                selector = self.elements[selector]

            logger.info(f"Executing step: {action} | Selector: {selector} | Value: {value}")

            self._execute_action(action, selector, value, step)

        except Exception as e:
            logger.error(f"Step execution failed: {str(e)}")
            self._capture_failure_evidence()
            raise
        finally:
            self._logger_step_duration()

    def _validate_step(self, step: Dict[str, Any]) -> None:
        if not step.get("action"):
            raise ValueError("Step action is missing")

        action = step["action"].lower()
        # 验证是否是支持的操作
        if not any(action in action_list for action_list in StepAction.__dict__.values()
                   if isinstance(action_list, list)):
            raise ValueError(f"不支持的操作类型: {action}")

        # 验证是否需要selector
        if action not in StepAction.NO_SELECTOR_ACTIONS and not step.get("selector"):
            raise ValueError(f"操作 {action} 需要提供 selector")

    def _execute_action(self, action: str, selector: str, value: str = None, step: Dict[str, Any] = None) -> None:
        """执行具体操作"""
        action = action.lower()
        with allure.step(f"执行步骤: {action}"):
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
                wait_time = int(float(step.get('value', '1')) * 1000) if step.get('value') else 1000
                self.ui_helper.wait_for_timeout(wait_time)

            elif action in StepAction.ASSERT_VISIBLE:
                self.ui_helper.assert_visible(selector)

            elif action in StepAction.ASSERT_TEXT:
                expected = step.get('expected', value)
                self.ui_helper.assert_text(selector, expected)

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


            elif action in StepAction.VERIFY:
                if 'expected' in step:
                    self.ui_helper.assert_text(selector, step['expected'])
                else:
                    self.ui_helper.assert_visible(selector)

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

            elif action in StepAction.EXIT_FRAME:
                self.ui_helper.exit_frame()


            elif action in StepAction.ACCEPT_ALERT:
                text = self.ui_helper.accept_alert(selector, value)

            elif action in StepAction.DISMISS_ALERT:
                self.ui_helper.dismiss_alert(selector)

            elif action in StepAction.SWITCH_WINDOW:
                url = step.get('url')
                title = step.get('title')
                self.ui_helper.switch_window(url, title)

            elif action in StepAction.CLOSE_WINDOW:
                self.ui_helper.close_window()

            elif action in StepAction.WAIT_FOR_NEW_WINDOW:
                new_page = self.ui_helper.wait_for_new_window()
                if 'variable_name' in step:
                    self.ui_helper.store_variable(step['variable_name'], new_page, step.get('scope', 'global'))

            elif action in StepAction.GET_ELEMENT_COUNT:
                count = self.ui_helper.get_element_count(selector)
                if 'variable_name' in step:
                    self.ui_helper.store_variable(step['variable_name'], str(count), step.get('scope', 'global'))

    def _capture_failure_evidence(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"./evidence/screenshots/failure_{timestamp}.png"
        self.page.screenshot(path=screenshot_path)
        allure.attach.file(screenshot_path, "失败截图", allure.attachment_type.PNG)

    def _logger_step_duration(self) -> None:
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            logger.info(f"Step execution took {duration:.2f} seconds")
