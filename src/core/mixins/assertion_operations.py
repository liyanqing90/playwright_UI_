"""
断言操作混入类
包含各种断言方法
"""
import re
import allure
from typing import List
from playwright.sync_api import expect
from src.assertion_manager import assertion_manager
from utils.logger import logger
from .decorators import check_and_screenshot


class AssertionOperationsMixin:
    """断言操作混入类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @check_and_screenshot("断言URL")
    def assert_url(self, expected: str):
        """断言当前URL"""
        expect(self.page).to_have_url(expected)

    @check_and_screenshot("断言文本")
    def assert_text(self, selector: str, expected: str):
        """断言元素文本（软断言）"""
        resolved_expected = self.variable_manager.replace_variables_refactored(expected)
        try:
            actual_text = self._locator(selector).first.inner_text()
            condition = actual_text == resolved_expected
            assertion_manager.soft_assert(
                condition=condition,
                message=f"文本断言失败: 期望 '{resolved_expected}', 实际 '{actual_text}'",
                expected=resolved_expected,
                actual=actual_text,
                step_description=f"断言元素 {selector} 的文本"
            )
            if not condition:
                # 软断言失败，但不抛出异常，继续执行
                return
        except Exception as e:
            # 如果获取文本失败，记录软断言失败
            assertion_manager.soft_assert(
                condition=False,
                message=f"获取元素文本失败: {str(e)}",
                expected=resolved_expected,
                actual="无法获取",
                step_description=f"断言元素 {selector} 的文本"
            )

        # 使用原有的expect进行实际断言（这里会抛出异常如果失败）
        expect(self._locator(selector).first).to_have_text(resolved_expected)

    @allure.step("硬断言元素文本")
    def hard_assert_text(self, selector: str, expected: str):
        """硬断言元素文本，失败时会终止测试执行"""
        resolved_expected = self.variable_manager.replace_variables_refactored(expected)

        try:
            actual_text = self._locator(selector).first.inner_text()
            condition = actual_text == resolved_expected

            # 使用断言管理器记录硬断言
            assertion_manager.hard_assert(
                condition=condition,
                message=f"硬断言文本失败: 期望 '{resolved_expected}', 实际 '{actual_text}'",
                expected=resolved_expected,
                actual=actual_text,
                step_description=f"硬断言元素 {selector} 的文本"
            )

        except Exception as e:
            # 如果获取文本失败，记录硬断言失败并抛出异常
            try:
                assertion_manager.hard_assert(
                    condition=False,
                    message=f"获取元素文本失败: {str(e)}",
                    expected=resolved_expected,
                    actual="无法获取",
                    step_description=f"硬断言元素 {selector} 的文本"
                )
            except AssertionError as assertion_error:
                # 截图
                if selector and hasattr(self.page, "locator"):
                    try:
                        # 尝试截取元素截图
                        screenshot = self.page.locator(selector).first.screenshot()
                    except Exception:
                        screenshot = self.page.screenshot()
                else:
                    # 如果没有选择器，直接截取页面
                    screenshot = self.page.screenshot()

                # 添加截图到报告
                allure.attach(
                    screenshot,
                    name="硬断言失败截图",
                    attachment_type=allure.attachment_type.PNG,
                )

                # 标记为硬断言异常
                setattr(assertion_error, "_hard_assert", True)
                logger.error(f"硬断言失败: {assertion_error}")
                raise assertion_error

    @check_and_screenshot("断言页面标题")
    def assert_title(self, expected: str):
        """断言页面标题"""
        expect(self.page).to_have_title(expected)

    @check_and_screenshot("断言元素数量")
    def assert_element_count(self, selector: str, expected: int):
        """断言元素数量"""
        try:
            expected = int(expected)
        except Exception:
            logger.error(f"断言元素数量失败: 期望数量 '{expected}' 不是有效的整数")
            raise

        expect(self._locator(selector)).to_have_count(expected)

    @check_and_screenshot("断言文本包含")
    def assert_text_contains(self, selector: str, expected: str):
        """断言元素文本包含指定内容"""
        resolved_expected = self.variable_manager.replace_variables_refactored(expected)
        expect(self._locator(selector).first).to_contain_text(resolved_expected)

    @check_and_screenshot("断言URL包含")
    def assert_url_contains(self, expected: str):
        """断言当前URL包含指定内容"""
        resolved_expected = self.variable_manager.replace_variables_refactored(expected)
        expect(self.page).to_have_url(re.compile(f".*{re.escape(resolved_expected)}.*"))

    @check_and_screenshot("断言元素存在")
    def assert_exists(self, selector: str):
        """断言元素存在于DOM中"""
        expect(self._locator(selector).first).to_be_attached()

    @check_and_screenshot("断言元素不存在")
    def assert_not_exists(self, selector: str):
        """断言元素不存在于DOM中"""
        expect(self._locator(selector).first).not_to_be_attached()

    @check_and_screenshot("断言元素启用状态")
    def assert_element_enabled(self, selector: str):
        """断言元素处于启用状态（非禁用）"""
        expect(self._locator(selector).first).to_be_enabled()

    @check_and_screenshot("断言元素禁用状态")
    def assert_element_disabled(self, selector: str):
        """断言元素处于禁用状态"""
        expect(self._locator(selector).first).to_be_disabled()

    @check_and_screenshot("断言元素可见性")
    def assert_visible(self, selector: str):
        """断言元素可见"""
        expect(self._locator(selector).first).to_be_visible()

    @check_and_screenshot("断言元素不可见")
    def assert_not_visible(self, selector: str):
        """断言元素不可见"""
        expect(self._locator(selector).first).not_to_be_visible()

    @check_and_screenshot("断言元素隐藏")
    def assert_be_hidden(self, selector: str):
        """断言元素隐藏"""
        expect(self.page.locator(selector)).to_be_hidden()

    @check_and_screenshot("断言元素属性")
    def assert_attribute(self, selector: str, attribute: str, expected: str):
        """断言元素属性值"""
        expect(self._locator(selector).first).to_have_attribute(attribute, expected)

    @check_and_screenshot("断言元素值")
    def assert_value(self, selector: str, expected: str):
        """断言元素值"""
        resolved_expected = self.variable_manager.replace_variables_refactored(expected)
        expect(self._locator(selector).first).to_have_value(resolved_expected)

    @check_and_screenshot("断言元素已选中")
    def assert_checked(self, selector: str):
        """断言元素已选择"""
        expect(self._locator(selector).first).to_be_checked()

    @check_and_screenshot("断言元素值列表")
    def assert_values(self, selector: str, expected: List[str]):
        """断言元素有多个值（适用于多选框等）"""
        resolved_values = [
            self.variable_manager.replace_variables_refactored(val) for val in expected
        ]
        expect(self.page.locator(selector)).to_have_values(resolved_values)

    @check_and_screenshot("断言元素有精确文本")
    def assert_exact_text(self, selector: str, expected: str):
        """断言元素有精确的文本（不包括子元素文本）"""
        resolved_expected = self.variable_manager.replace_variables_refactored(expected)
        expect(self._locator(selector).first).to_have_text(
            resolved_expected, use_inner_text=True
        )

    @check_and_screenshot("断言元素匹配文本正则")
    def assert_text_matches(self, selector: str, pattern: str):
        """断言元素文本匹配正则表达式"""
        expect(self._locator(selector).first).to_have_text(re.compile(pattern))
