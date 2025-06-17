#!/usr/bin/env python3
"""
元素操作服务模块

提供页面元素操作的核心功能。
已迁移到使用通用操作装饰器系统。
"""

import time
from typing import Protocol, Any, Optional

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from config.constants import DEFAULT_TIMEOUT
from utils.logger import logger
from .base_service import BaseService
from .operation_decorator import operation_decorator


class ElementOperations(Protocol):
    """元素操作协议

    定义元素操作的标准接口。
    """

    def click(
        self, page: Page, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> None:
        """点击元素"""
        ...

    def fill(
        self,
        page: Page,
        selector: str,
        value: str,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> None:
        """填写文本"""
        ...

    def double_click(
        self, page: Page, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> None:
        """双击元素"""
        ...

    def hover(
        self, page: Page, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> None:
        """悬停元素"""
        ...

    def get_text(
        self, page: Page, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> str:
        """获取元素文本"""
        ...

    def get_attribute(
        self,
        page: Page,
        selector: str,
        attribute: str,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> Optional[str]:
        """获取元素属性"""
        ...

    def is_visible(
        self, page: Page, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> bool:
        """检查元素是否可见"""
        ...

    def is_enabled(
        self, page: Page, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> bool:
        """检查元素是否启用"""
        ...


class ElementService(BaseService):
    """元素操作服务实现

    提供页面元素操作的具体实现，集成性能监控和错误处理。

    示例:
        ```python
        element_service = container.resolve(ElementService)
        element_service.click(page, "#submit-button")
        ```
    """

    def __init__(self, performance_manager=None, variable_manager=None):
        """初始化元素服务

        Args:
            performance_manager: 性能管理器
            variable_manager: 变量管理器
        """
        super().__init__(performance_manager, variable_manager)

    @operation_decorator(operation_type="点击元素", auto_screenshot=False)
    def click(
        self, page: Page, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> None:
        """点击指定的元素

        Args:
            page: Playwright页面对象
            selector: CSS选择器
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT

        Raises:
            PlaywrightTimeoutError: 如果元素超时未出现
        """
        locator = self._get_locator(page, selector, timeout)
        locator.first.click(timeout=timeout)

    @operation_decorator(operation_type="填写文本", auto_screenshot=False)
    def fill(
        self,
        page: Page,
        selector: str,
        value: str,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> None:
        """在输入框中填写文本

        Args:
            page: Playwright页面对象
            selector: CSS选择器
            value: 要填写的文本
            timeout: 超时时间（毫秒）
        """
        if value is not None:
            value = str(value)

        locator = self._get_locator(page, selector)
        locator.first.fill(value, timeout=timeout)

    @operation_decorator(operation_type="双击元素", auto_screenshot=False)
    def double_click(
        self, page: Page, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> None:
        """双击元素

        Args:
            page: Playwright页面对象
            selector: CSS选择器
            timeout: 超时时间（毫秒）
        """
        locator = self._get_locator(page, selector)
        locator.first.dblclick(timeout=timeout)

    def hover(
        self, page: Page, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> None:
        """悬停在元素上

        Args:
            page: Playwright页面对象
            selector: CSS选择器
            timeout: 超时时间（毫秒）
        """
        start_time = time.time()

        try:
            self._log_operation("hover", f"selector: {selector}")

            locator = self._get_locator(page, selector)
            locator.first.hover(timeout=timeout)

            duration = time.time() - start_time
            self._record_operation("hover", duration, True)

            logger.debug(f"成功悬停元素: {selector}")

        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("hover", duration, False)
            logger.error(f"悬停元素失败: {selector}, 错误: {e}")
            raise

    def get_text(
        self, page: Page, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> str:
        """获取元素文本内容

        Args:
            page: Playwright页面对象
            selector: CSS选择器
            timeout: 超时时间（毫秒）

        Returns:
            str: 元素的文本内容
        """
        start_time = time.time()

        try:
            self._log_operation("get_text", f"selector: {selector}")

            locator = self._get_locator(page, selector)
            # 先确保元素可见
            text = locator.first.text_content(timeout=timeout)

            duration = time.time() - start_time
            self._record_operation("get_text", duration, True)

            logger.debug(f"成功获取文本: {selector} = {text}")
            return text or ""

        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("get_text", duration, False)
            logger.error(f"获取文本失败: {selector}, 错误: {e}")
            raise

    def get_attribute(
        self,
        page: Page,
        selector: str,
        attribute: str,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> Optional[str]:
        """获取元素属性值

        Args:
            page: Playwright页面对象
            selector: CSS选择器
            attribute: 属性名
            timeout: 超时时间（毫秒）

        Returns:
            Optional[str]: 属性值，如果属性不存在则返回None
        """
        start_time = time.time()

        try:
            self._log_operation(
                "get_attribute", f"selector: {selector}, attribute: {attribute}"
            )

            locator = self._get_locator(page, selector)
            value = locator.first.get_attribute(attribute, timeout=timeout)

            duration = time.time() - start_time
            self._record_operation("get_attribute", duration, True)

            logger.debug(f"成功获取属性: {selector}.{attribute} = {value}")
            return value

        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("get_attribute", duration, False)
            logger.error(f"获取属性失败: {selector}.{attribute}, 错误: {e}")
            raise

    def is_visible(
        self, page: Page, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> bool:
        """检查元素是否可见

        Args:
            page: Playwright页面对象
            selector: CSS选择器
            timeout: 超时时间（毫秒）

        Returns:
            bool: 元素是否可见
        """
        try:
            timeout = timeout or 1000  # 可见性检查使用较短超时
            locator = self._get_locator(page, selector)
            return locator.first.is_visible(timeout=timeout)
        except:
            return False

    def is_enabled(
        self, page: Page, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> bool:
        """检查元素是否启用

        Args:
            page: Playwright页面对象
            selector: CSS选择器
            timeout: 超时时间（毫秒）

        Returns:
            bool: 元素是否启用
        """
        try:
            timeout = timeout or 1000
            locator = self._get_locator(page, selector)
            return locator.first.is_enabled(timeout=timeout)
        except:
            return False
