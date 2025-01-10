import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import allure

log = logging.getLogger(__name__)


class StepAction:
    # 定义操作类型及其别名
    NAVIGATE = ['navigate', 'goto', '打开', '访问']
    CLICK = ['click', '点击']
    FILL = ['fill', '输入']
    PRESS_KEY = ['press_key', '按键']
    WAIT = ['wait', '等待']
    ASSERT_VISIBLE = ['assert_visible', '验证可见']
    ASSERT_TEXT = ['assert_text', 'assertion', '验证文本']
    STORE_VARIABLE = ['store_variable', '存储变量']
    STORE_TEXT = ['store_text', '存储文本']
    STORE_ATTRIBUTE = ['store_attribute', '存储属性']
    REFRESH = ['refresh', '刷新']
    VERIFY = ['verify', '验证']

    # 不需要selector的操作
    NO_SELECTOR_ACTIONS = NAVIGATE + WAIT + REFRESH


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

            log.info(f"Executing step: {action} | Selector: {selector} | Value: {value}")

            self._execute_action(action, selector, value, step)

        except Exception as e:
            log.error(f"Step execution failed: {str(e)}")
            self._capture_failure_evidence()
            raise
        finally:
            self._log_step_duration()

    def _validate_step(self, step: Dict[str, Any]) -> None:
        if not step.get("action"):
            raise ValueError("Step action is missing")

        action = step["action"].lower()
        # 验证是否是支持的操作
        if not any(action in action_list for action_list in vars(StepAction).values()
                   if isinstance(action_list, list)):
            raise ValueError(f"不支持的操作类型: {action}")

        # 验证是否需要selector
        if action not in StepAction.NO_SELECTOR_ACTIONS and not step.get("selector"):
            raise ValueError(f"操作 {action} 需要提供 selector")

    def _execute_action(self, action: str, selector: str, value: str, step: Dict[str, Any]) -> None:
        action = action.lower()
        with allure.step(f"执行步骤: {action}"):
            if action in StepAction.NAVIGATE:
                self.ui_helper.goto(value)

            elif action in StepAction.CLICK:
                self.ui_helper.click(selector)

            elif action in StepAction.FILL:
                self.ui_helper.fill(selector, value)

            elif action in StepAction.PRESS_KEY:
                self.ui_helper.press_key(selector, step.get('key', value))

            elif action in StepAction.WAIT:
                wait_time = int(float(step.get('value', '1')) * 1000) if step.get('value') else 1000
                self.ui_helper.wait_timeout(wait_time)

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

    def _capture_failure_evidence(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"./evidence/screenshots/failure_{timestamp}.png"
        self.page.screenshot(path=screenshot_path)
        allure.attach.file(screenshot_path, "失败截图", allure.attachment_type.PNG)

    def _log_step_duration(self) -> None:
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            log.info(f"Step execution took {duration:.2f} seconds")
