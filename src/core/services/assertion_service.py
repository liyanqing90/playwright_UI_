#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
断言服务模块

提供页面断言相关的功能，支持软断言和硬断言。
包含统一的断言装饰器，类似于其他service的操作装饰器。
"""

import functools
import time
from typing import Any, Optional, Protocol, Tuple

import allure
import pytest_check as check
from playwright.sync_api import Page

from config.constants import DEFAULT_TIMEOUT
from src.assertion_manager import assertion_manager
from src.core.services.base_service import BaseService
from utils.logger import logger
from .operation_decorator import operation_decorator  # 导入通用操作装饰器


def _parse_error_message(
    error_str: str,
    expected: Any = None,
    selector: str = None,
    actual_value: Any = None,
) -> Tuple[str, Any, Any]:
    """解析断言错误消息，提取期望值和实际值

    Args:
        error_str: 原始错误消息
        expected: 期望值
        selector: 元素选择器
        actual_value: 实际值

    Returns:
        (格式化后的错误消息, 提取的期望值, 提取的实际值)
    """
    extracted_expected = expected
    extracted_actual = actual_value

    # 尝试从错误中提取期望值和实际值
    # 检查常见的Playwright错误模式
    if (
        extracted_actual is None
        and "expect" in error_str
        and "to." in error_str
        and "received" in error_str
    ):
        # 例如：expect(received).to.equal(expected)
        parts = error_str.split("receive")
        if len(parts) > 1 and "Received:" in parts[1]:
            actual_part = parts[1].split("Received:")[1].strip()
            extracted_actual = actual_part

    # 格式化错误消息
    formatted_error = "断言失败"
    if selector:
        formatted_error += f"，元素: {selector}"
    if expected:
        formatted_error += f"，期望值: {expected}"
    if extracted_actual:
        formatted_error += f"，实际值: {extracted_actual}"

    return formatted_error, extracted_expected, extracted_actual


def _get_screenshot(page: Page, selector: str = None) -> Optional[bytes]:
    """获取指定元素或页面的截图

    Args:
        page: Playwright页面对象
        selector: 元素选择器，如果为None则截取整个页面

    Returns:
        bytes: 截图数据，如果失败则返回None
    """
    try:
        # 强制尝试对元素截图
        if selector:
            try:
                element = page.locator(selector)
                # 先检查元素是否存在
                if element.count() > 0:
                    # 确保元素在视口内且可见
                    element = element.first
                    element.scroll_into_view_if_needed()
                    # 等待元素完全可见
                    page.wait_for_timeout(100)  # 短暂等待渲染完成
                    if element.is_visible():
                        logger.debug(f"正在截取元素: {selector} 的截图")
                        return element.screenshot()
                    else:
                        logger.warning(f"元素不可见，无法截图: {selector}")
                else:
                    logger.warning(f"未找到元素，无法截图: {selector}")
            except Exception as e:
                logger.warning(f"元素截图失败: {e}，将使用页面截图")

        # 如果元素截图失败或没有指定元素，使用页面截图
        logger.debug("正在截取页面截图")
        return page.screenshot()
    except Exception as e:
        logger.error(f"截图失败: {e}")
        return None


def assertion_decorator(assertion_type: str = "soft", description: str = "断言操作"):
    """
    统一断言装饰器

    Args:
        assertion_type: 断言类型，"soft"或"hard"
        description: 断言操作的描述
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, page: Page, *args, **kwargs):
            # 构建操作描述
            operation_description = description
            selector = kwargs.get("selector", args[0] if len(args) > 0 else None)
            expected = kwargs.get(
                "expected",
                (
                    args[1]
                    if len(args) > 1
                    else kwargs.get(
                        "text", kwargs.get("url_part", kwargs.get("title_part", None))
                    )
                ),
            )

            if selector:
                operation_description += f"，元素: {selector}"
            if expected:
                operation_description += f"，期望值: {expected}"

            # 记录操作
            if hasattr(self, "_log_operation"):
                self._log_operation(func.__name__, operation_description)

            start_time = time.time()

            try:
                with allure.step(f"{operation_description}"):
                    # 执行原始断言函数
                    try:
                        return func(self, page, *args, **kwargs)

                    except AssertionError as e:
                        # 处理断言失败
                        error_str = str(e)

                        # 尝试获取真实的实际值
                        actual_value = None
                        if selector:
                            try:
                                # 尝试获取元素的实际文本值
                                error_str = str(e)
                                logger.debug(f"原始断言错误: {error_str}")
                                # 尝试提取 Locator expected 和 Actual value 部分
                                import re

                                # 多种正则表达式模式来匹配不同格式的错误消息
                                patterns = [
                                    r"实际结果:\s*'([^']*)'",  # 匹配单引号包围的实际值
                                    r"实际结果:\s*([^\n,]*)",  # 匹配到换行或逗号为止的实际值
                                    r"实际\s*'([^']*)'",  # 匹配 "实际 'value'" 格式
                                    r"actual\s*'([^']*)'",  # 匹配英文格式
                                    r"received\s*'([^']*)'",  # 匹配 received 格式
                                ]

                                for pattern in patterns:
                                    actual_match = re.search(
                                        pattern, error_str, re.IGNORECASE
                                    )
                                    if actual_match:
                                        actual_value = actual_match.group(1)
                                        logger.debug(
                                            f"通过模式 '{pattern}' 匹配到实际值: {actual_value}"
                                        )
                                        break

                            except Exception as text_error:
                                logger.debug(f"获取元素实际值失败: {text_error}")
                                actual_value = "获取失败"

                            # 硬断言会抛出异常，这里先捕获，后面再选择是否抛出

                        # 使用更新后的错误解析函数
                        simplified_error, extracted_expected, extracted_actual = (
                            _parse_error_message(
                                error_str,
                                expected,
                                selector,
                                actual_value,
                            )
                        )

                        # 使用解析后的实际值
                        actual_value = extracted_actual or actual_value

                        # 获取截图
                        screenshot = _get_screenshot(page, selector)

                        # 记录性能指标
                        if hasattr(self, "_record_operation"):
                            duration = time.time() - start_time
                            self._record_operation(func.__name__, duration, False)

                        # 记录断言失败
                        assertion_manager.record_assertion(
                            assertion_type=assertion_type,
                            condition=False,
                            message=simplified_error,
                            expected=extracted_expected or expected,
                            actual=actual_value or extracted_actual or "断言失败",
                            step_description=operation_description,
                            screenshot=screenshot,
                        )

                        # 记录详细信息到allure
                        import json

                        allure.attach(
                            json.dumps(simplified_error, ensure_ascii=False, indent=2),
                            name="断言详情",
                            attachment_type=allure.attachment_type.JSON,
                        )

                        check.fail(simplified_error)
                        raise AssertionError(simplified_error)
            except AssertionError as e:
                if assertion_type == "hard":
                    raise e
                return None
            except Exception as e:

                # 更新StepExecutor状态
                if not hasattr(e, "_logged"):
                    setattr(e, "_logged", True)
                    from src.automation.step_executor import StepExecutor
                    import gc

                    # 搜索内存中的所有StepExecutor实例
                    for obj in gc.get_objects():
                        if isinstance(obj, StepExecutor):
                            obj.step_has_error = True
                            obj.has_error = True
                            setattr(obj, "_last_assertion_error", str(e))
                            break

                raise e

        return wrapper

    return decorator


# 与通用操作装饰器的配合使用示例
# 注意：assertion_decorator 专门用于断言操作，operation_decorator 用于其他操作
# 两者可以在同一个service中配合使用


# 示例：在AssertionService中使用operation_decorator处理非断言操作
class AssertionServiceExample:
    """展示如何在断言服务中配合使用两种装饰器"""

    # 断言操作使用 assertion_decorator
    @assertion_decorator("soft", "验证元素文本")
    def assert_text_contains(self, page: Page, selector: str, expected: str):
        """断言元素包含指定文本"""
        assert expected in (
            actual := page.locator(selector).text_content()
        ), f"期望文本 '{expected}' 不在实际文本 '{actual}' 中"

    # 辅助操作使用 operation_decorator
    @operation_decorator(
        operation_type="辅助操作", auto_screenshot=False, include_performance=True
    )
    def get_element_text_for_assertion(self, page: Page, selector: str) -> str:
        """获取元素文本，用于后续断言"""
        return page.locator(selector).text_content() or ""

    # 复合操作：结合操作和断言
    @operation_decorator(
        operation_type="复合验证", auto_screenshot=True, include_performance=True
    )
    def wait_and_assert_element_visible(
        self, page: Page, selector: str, timeout: int = 5000
    ):
        """等待元素可见并进行断言验证"""
        # 先等待元素
        page.locator(selector).wait_for(state="visible", timeout=timeout)

        # 然后使用断言装饰器进行验证
        @assertion_decorator("hard", "验证元素可见性")
        def _assert_visible(self, page: Page, selector: str):
            assert page.locator(selector).is_visible(), f"元素 {selector} 不可见"

        _assert_visible(self, page, selector)


# 提供两个便捷装饰器
def soft_assert(description: str = "软断言"):
    """
    软断言装饰器，失败时记录但继续执行

    Args:
        description: 断言描述
    """
    return assertion_decorator("soft", description)


def hard_assert(description: str = "硬断言"):
    """
    硬断言装饰器，失败时终止执行

    Args:
        description: 断言描述
    """
    return assertion_decorator("hard", description)


class AssertionOperations(Protocol):
    """断言操作协议"""

    def assert_element_visible(
        self,
        page: Page,
        selector: str,
        message: Optional[str] = None,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> None:
        """断言元素可见"""
        ...

    def assert_element_hidden(self, page: Page, selector: str) -> None:
        """断言元素隐藏"""
        ...

    def assert_text_contains(self, page: Page, selector: str, text: str) -> None:
        """断言元素包含指定文本"""
        ...

    def assert_url_contains(self, page: Page, url_part: str) -> None:
        """断言URL包含指定部分"""
        ...

    def assert_title_contains(self, page: Page, title_part: str) -> None:
        """断言页面标题包含指定文本"""
        ...

    def assert_title(self, page: Page, title: str) -> None:
        """断言页面标题"""
        ...

    def assert_attribute(
        self, page: Page, selector: str, attribute: str, expected: str
    ) -> None:
        """断言元素属性等于指定值"""
        ...

    def assert_element_count(self, page: Page, selector: str, count: int) -> None:
        """断言元素数量等于指定值"""
        ...

    def assert_url(self, page: Page, url: str) -> None:
        """断言页面URL等于指定值"""
        ...

    def assert_value(self, page: Page, selector: str, expected: str) -> None:
        """断言元素值等于指定值"""
        ...

    def assert_exists(self, page: Page, selector: str) -> None:
        """断言元素存在"""
        ...

    def assert_not_exists(self, page: Page, selector: str) -> None:
        """断言元素不存在"""
        ...

    def assert_element_enabled(self, page: Page, selector: str) -> None:
        """断言元素启用"""
        ...

    def assert_element_disabled(self, page: Page, selector: str) -> None:
        """断言元素禁用"""
        ...

    def assert_values(self, page: Page, selector: str, expected: list) -> None:
        """断言元素多个值"""
        ...

    def assert_text(self, page: Page, selector: str, expected: str) -> None:
        """断言元素文本"""
        ...

    def assert_visible(self, page: Page, selector: str) -> None:
        """断言元素可见"""
        ...


class AssertionService(BaseService, AssertionOperations):
    """断言服务实现"""

    def setup(self):
        """初始化断言服务"""
        logger.info("断言服务初始化完成")

    def cleanup(self):
        """清理断言服务"""
        logger.info("断言服务清理完成")

    def get_all_failed_assertions(self) -> list:
        """获取所有失败的断言

        Returns:
            失败断言列表
        """
        return assertion_manager.get_failed_assertions()

    def get_assertion_stats(self) -> dict:
        """获取断言统计信息

        Returns:
            断言统计字典
        """
        stats = assertion_manager.get_stats()
        return {
            "total": stats.total_assertions,
            "passed": stats.passed_assertions,
            "failed": stats.failed_assertions,
            "failed_soft": stats.failed_soft_assertions,
            "failed_hard": stats.failed_hard_assertions,
        }

    @soft_assert("断言元素可见")
    def assert_element_visible(
        self,
        page: Page,
        selector: str,
        message: Optional[str] = None,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> None:
        """断言元素可见

        Args:
            page: Playwright页面对象
            selector: CSS选择器
            message: 自定义错误消息
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT

        Returns:
            None 如果断言成功，否则抛出异常
        """
        specific_message = message or f"元素应该可见：{selector}"

        start_time = time.time()

        try:
            # 等待元素出现
            page.locator(selector).first.wait_for(state="visible", timeout=timeout)
            assert page.locator(
                selector
            ).first.is_visible(), (
                f"元素可见性断言失败: 期望结果: '可见', 实际结果: '不可见' ({selector})"
            )

            if hasattr(self, "_record_operation"):
                duration = time.time() - start_time
                self._record_operation("assert_element_visible", duration, True)
            return
        except Exception as e:
            error_msg = (
                f"{specific_message}\n期望值: 元素可见\n实际值: 元素不可见 ({selector})"
            )
            if hasattr(self, "_record_operation"):
                duration = time.time() - start_time
                self._record_operation("assert_element_visible", duration, False)
            raise AssertionError(error_msg)

    @hard_assert("断言元素可见")
    def assert_element_visible_hard(
        self,
        page: Page,
        selector: str,
        message: Optional[str] = None,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> None:
        """断言元素可见（硬断言，失败时终止执行）

        Args:
            page: playwright Page 对象
            selector: 元素选择器
            message: 可选断言消息
            timeout: 超时时间（毫秒）

        Returns:
            None 如果断言成功，否则抛出异常
        """
        # 与软断言版本共用相同实现
        return self.assert_element_visible(page, selector, message, timeout)

    @soft_assert("断言元素隐藏")
    def assert_element_hidden(self, page: Page, selector: str):
        """断言元素隐藏"""
        assert not page.locator(
            selector
        ).first.is_visible(), (
            f"元素隐藏性断言失败: 期望结果: '隐藏', 实际结果: '可见' ({selector})"
        )

    @soft_assert("断言元素包含指定文本")
    def assert_text_contains(self, page: Page, selector: str, text: str):
        """断言元素包含指定文本"""
        assert text in (
            actual := page.locator(selector).first.inner_text()
        ), f"文本包含断言失败: 期望包含 '{text}', 实际 '{actual}' ({selector})"

    @soft_assert("断言URL包含指定部分")
    def assert_url_contains(self, page: Page, url_part: str):
        """断言URL包含指定部分"""
        try:
            url = page.url
            assert url_part in url, f"URL不包含指定部分: 期望包含 '{url_part}'"
        except Exception as e:
            raise AssertionError(f"URL不包含指定部分: 期望包含 '{url_part}'")

    @hard_assert("断言URL包含指定部分")
    def assert_url_contains_hard(self, page: Page, url_part: str):
        """断言URL包含指定部分（硬断言）"""
        return self.assert_url_contains(page, url_part)

    @soft_assert("断言页面标题包含指定文本")
    def assert_title_contains(self, page: Page, title_part: str):
        """断言页面标题包含指定文本"""
        try:
            title = page.title()
            assert (
                title_part in title
            ), f"页面标题不包含指定文本: 期望包含 '{title_part}'"
        except Exception as e:
            raise AssertionError(f"页面标题不包含指定文本: 期望包含 '{title_part}'")

    @soft_assert("断言页面标题")
    def assert_title(self, page: Page, title: str):
        """断言页面标题"""
        assert (
            actual := page.title()
        ) == title, f"页面标题断言失败: 期望结果: '{title}', 实际结果: '{actual}'"

    @hard_assert("断言页面标题")
    def assert_title_hard(self, page: Page, title: str):
        """断言页面标题（硬断言）"""
        return self.assert_title(page, title)

    @soft_assert("断言元素属性等于指定值")
    def assert_attribute(
        self, page: Page, selector: str, attribute: str, expected: str
    ):
        """断言元素属性等于指定值"""
        assert (
            actual := page.locator(selector).first.get_attribute(attribute)
        ) == expected, f"元素属性断言失败: {selector}, 属性: {attribute}, 期望结果: '{expected}', 实际结果: '{actual}'"

    @soft_assert("断言元素数量等于指定值")
    def assert_element_count(self, page: Page, selector: str, count: int):
        """断言元素数量等于指定值"""
        assert (
            actual := page.locator(selector).count()
        ) == count, (
            f"元素数量断言失败: {selector}, 期望结果: {count}, 实际结果: {actual}"
        )

    @soft_assert("断言页面URL等于指定值")
    def assert_url(self, page: Page, url: str):
        """断言页面URL等于指定值"""
        assert (
            actual := page.url
        ) == url, f"页面URL断言失败: 期望结果: '{url}', 实际结果: '{actual}'"

    @hard_assert("断言页面URL等于指定值")
    def assert_url_hard(self, page: Page, url: str):
        """断言页面URL等于指定值（硬断言）"""
        return self.assert_url(page, url)

    @soft_assert("断言元素值等于指定值")
    def assert_value(self, page: Page, selector: str, expected: str):
        """断言元素值等于指定值"""
        assert (
            actual := page.locator(selector).first.input_value()
        ) == expected, (
            f"元素值断言失败: {selector}, 期望结果: '{expected}', 实际结果: '{actual}'"
        )

    @soft_assert("断言元素存在")
    def assert_exists(self, page: Page, selector: str):
        """断言元素存在"""
        assert (
            actual := page.locator(selector).count()
        ) >= 1, f"元素存在断言失败: {selector}, 期望结果: '存在', 实际结果: '不存在' (数量: {actual})"

    @hard_assert("断言元素存在")
    def assert_exists_hard(self, page: Page, selector: str):
        """断言元素存在（硬断言，失败时终止执行）"""
        return self.assert_exists(page, selector)

    @soft_assert("断言元素不存在")
    def assert_not_exists(self, page: Page, selector: str):
        """断言元素不存在"""
        assert (
            actual := page.locator(selector).count()
        ) == 0, f"元素不存在断言失败: {selector}, 期望结果: '不存在', 实际结果: '存在' (数量: {actual})"

    @soft_assert("断言元素启用")
    def assert_element_enabled(self, page: Page, selector: str):
        """断言元素启用"""
        assert page.locator(
            selector
        ).first.is_enabled(), (
            f"元素启用断言失败: {selector}, 期望结果: '启用', 实际结果: '禁用'"
        )

    @soft_assert("断言元素禁用")
    def assert_element_disabled(self, page: Page, selector: str):
        """断言元素禁用"""
        assert not page.locator(
            selector
        ).first.is_enabled(), (
            f"元素禁用断言失败: {selector}, 期望结果: '禁用', 实际结果: '启用'"
        )

    @soft_assert("断言元素多个值")
    def assert_values(self, page: Page, selector: str, expected: list):
        """断言元素多个值"""
        assert (
            actual := [
                page.locator(selector).nth(i).input_value()
                for i in range(page.locator(selector).count())
            ]
        ) == expected, (
            f"元素多个值断言失败: {selector}, 期望结果: {expected}, 实际结果: {actual}"
        )

    @soft_assert("断言元素文本")
    def assert_text(self, page: Page, selector: str, expected: str):
        """断言元素文本（软断言）"""

        assert (
            actual := page.locator(selector).first.inner_text()
        ) == expected, f"文本断言失败: 期望结果: '{expected}', 实际结果: '{actual}'"

    @hard_assert("断言元素文本")
    def assert_text_hard(self, page: Page, selector: str, expected: str):
        """断言元素文本（硬断言，失败时终止执行）"""
        assert (
            actual := page.locator(selector).first.inner_text()
        ) == expected, f"文本断言失败: 期望 '{expected}', 实际 '{actual}'"

    @soft_assert("断言元素可见")
    def assert_visible(self, page: Page, selector: str):
        """断言元素可见"""
        assert page.locator(
            selector
        ).first.is_visible(), (
            f"元素可见性断言失败: {selector}, 期望结果: '可见', 实际结果: '不可见'"
        )

    @hard_assert("断言元素可见")
    def assert_visible_hard(self, page: Page, selector: str):
        """断言元素可见（硬断言）"""
        return self.assert_visible(page, selector)
