# -*- coding: utf-8 -*-
"""
命令适配器：将命令模式转换为BasePage方法调用
"""

from typing import Any, Dict

from src.core import BasePage


class CommandAdapter:
    """命令适配器：将命令模式转换为BasePage方法调用"""

    def __init__(self, base_page: BasePage):
        self.base_page = base_page

    def execute_action(
        self, action: str, selector: str, value: Any, step: Dict[str, Any]
    ):
        """执行动作"""
        action_lower = action.lower()

        # 元素操作
        if action_lower == "click":
            return self.base_page.click(selector)
        elif action_lower == "fill":
            return self.base_page.fill(selector, value)
        elif action_lower == "press_key":
            return self.base_page.press_key(selector, step.get("key", value))
        elif action_lower == "hover":
            return self.base_page.hover(selector)
        elif action_lower == "double_click":
            return self.base_page.double_click(selector)
        elif action_lower == "right_click":
            return self.base_page.right_click(selector)
        elif action_lower == "clear":
            return self.base_page.clear(selector)
        elif action_lower == "type":
            delay = int(step.get("delay", 100))
            return self.base_page.type(selector, value, delay)
        elif action_lower == "select_option":
            return self.base_page.select_option(selector, value)
        elif action_lower == "upload_file":
            return self.base_page.upload_file(selector, value)

        # 等待操作
        elif action_lower == "wait":
            timeout = int(value) * 1000 if value else 1000
            return self.base_page.wait_for_timeout(timeout)
        elif action_lower == "wait_for_network_idle":
            timeout = int(step.get("timeout", 30000))
            return self.base_page.wait_for_load_state("networkidle")
        elif action_lower == "wait_for_element_hidden":
            timeout = int(step.get("timeout", 30000))
            return self.base_page.wait_for_element_hidden(selector, timeout)
        elif action_lower == "wait_for_element_clickable":
            timeout = int(step.get("timeout", 30000))
            return self.base_page.wait_for_element_clickable(selector, timeout)
        elif action_lower == "wait_for_element_text":
            expected = step.get("expected", value)
            timeout = int(step.get("timeout", 30000))
            return self.base_page.wait_for_element_text(selector, expected, timeout)

        # 导航操作
        elif action_lower == "navigate":
            return self.base_page.navigate(value)
        elif action_lower == "refresh":
            return self.base_page.refresh()
        elif action_lower == "pause":
            return self.base_page.page.pause()

        # 断言操作
        elif action_lower == "assert_text":
            expected = step.get("expected", value)
            return self.base_page.assert_text(selector, expected)
        elif action_lower == "hard_assert_text":
            expected = step.get("expected", value)
            return self.base_page.hard_assert_text(selector, expected)
        elif action_lower == "assert_text_contains":
            expected = step.get("expected", value)
            return self.base_page.assert_text_contains(selector, expected)
        elif action_lower == "assert_url":
            expected = step.get("expected", value)
            return self.base_page.assert_url(expected)
        elif action_lower == "assert_visible":
            return self.base_page.assert_visible(selector)
        elif action_lower == "assert_be_hidden":
            return self.base_page.assert_be_hidden(selector)
        elif action_lower == "assert_exists":
            return self.base_page.assert_exists(selector)
        elif action_lower == "assert_not_exists":
            return self.base_page.assert_not_exists(selector)

        # 其他操作
        elif action_lower == "scroll_into_view":
            return self.base_page.scroll_into_view(selector)
        elif action_lower == "focus":
            return self.base_page.focus(selector)
        elif action_lower == "blur":
            return self.base_page.blur(selector)

        else:
            raise ValueError(f"不支持的动作: {action}")
