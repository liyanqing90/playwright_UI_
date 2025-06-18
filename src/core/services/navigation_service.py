#!/usr/bin/env python3
"""
导航操作服务模块

提供页面导航相关的功能。
已迁移到使用通用操作装饰器系统。
"""

import time
from typing import Protocol, Optional

from playwright.sync_api import Page

from config.constants import DEFAULT_TIMEOUT
from utils.logger import logger
from .base_service import BaseService
from .operation_decorator import operation_decorator


class NavigationOperations(Protocol):
    """导航操作协议"""

    def goto(
        self, page: Page, url: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> None:
        """导航到指定URL"""
        ...

    def go_back(self, page: Page, timeout: Optional[int] = DEFAULT_TIMEOUT) -> None:
        """后退"""
        ...

    def go_forward(self, page: Page, timeout: Optional[int] = DEFAULT_TIMEOUT) -> None:
        """前进"""
        ...

    def reload(self, page: Page, timeout: Optional[int] = DEFAULT_TIMEOUT) -> None:
        """刷新页面"""
        ...

    def get_url(self, page: Page) -> str:
        """获取当前URL"""
        ...

    def get_title(self, page: Page) -> str:
        """获取页面标题"""
        ...


class NavigationService(BaseService):
    """导航操作服务实现"""

    def __init__(self, performance_manager=None, variable_manager=None):
        super().__init__(performance_manager)
        self.variable_manager = variable_manager

    @operation_decorator(operation_type="访问", auto_screenshot=False)
    def goto(
        self, page: Page, url: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> None:
        """导航到指定URL

        Args:
            page: Playwright页面对象
            url: 目标URL
            timeout: 超时时间（毫秒）
        """
        # 增加超时时间并使用更宽松的等待策略
        page.goto(url, wait_until="domcontentloaded")

    @operation_decorator(operation_type="页面后退", auto_screenshot=False)
    def go_back(self, page: Page, timeout: Optional[int] = DEFAULT_TIMEOUT) -> None:
        """后退到上一页

        Args:
            page: Playwright页面对象
            timeout: 超时时间（毫秒）
        """
        page.go_back(timeout=timeout, wait_until="networkidle")

    @operation_decorator(operation_type="页面前进", auto_screenshot=False)
    def go_forward(self, page: Page, timeout: Optional[int] = DEFAULT_TIMEOUT) -> None:
        """前进到下一页

        Args:
            page: Playwright页面对象
            timeout: 超时时间（毫秒）
        """
        page.go_forward(timeout=timeout, wait_until="networkidle")

    @operation_decorator(operation_type="页面刷新", auto_screenshot=False)
    def reload(self, page: Page, timeout: Optional[int] = DEFAULT_TIMEOUT) -> None:
        """刷新当前页面

        Args:
            page: Playwright页面对象
            timeout: 超时时间（毫秒）
        """
        page.reload(timeout=timeout, wait_until="networkidle")

    def get_url(self, page: Page) -> str:
        """获取当前页面URL

        Args:
            page: Playwright页面对象

        Returns:
            str: 当前页面URL
        """
        try:
            url = page.url
            self._log_operation("get_url", f"url: {url}")
            logger.debug(f"当前URL: {url}")
            return url
        except Exception as e:
            logger.error(f"获取URL失败: {e}")
            raise

    def get_title(self, page: Page) -> str:
        """获取页面标题

        Args:
            page: Playwright页面对象

        Returns:
            str: 页面标题
        """
        try:
            title = page.title()
            self._log_operation("get_title", f"title: {title}")
            logger.debug(f"页面标题: {title}")
            return title
        except Exception as e:
            logger.error(f"获取页面标题失败: {e}")
            raise

    def wait_for_load_state(
        self,
        page: Page,
        state: str = "networkidle",
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> None:
        """等待页面加载状态

        Args:
            page: Playwright页面对象
            state: 等待的状态 ('load', 'domcontentloaded', 'networkidle')
            timeout: 超时时间（毫秒）
        """
        start_time = time.time()

        try:
            self._log_operation("wait_for_load_state", f"state: {state}")

            page.wait_for_load_state(state, timeout=timeout)

            duration = time.time() - start_time
            self._record_operation("wait_for_load_state", duration, True)

            logger.debug(f"页面加载状态达到: {state}")

        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("wait_for_load_state", duration, False)
            logger.error(f"等待页面加载状态失败: {state}, 错误: {e}")
            raise
