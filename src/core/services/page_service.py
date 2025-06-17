"""页面服务模块

提供页面级别的复合操作，整合多个基础服务。
"""

from typing import Protocol, Optional, Any, Dict

from playwright.sync_api import Page

from config.constants import DEFAULT_TIMEOUT
from .assertion_service import AssertionOperations
from .base_service import BaseService
from .element_service import ElementOperations
from .navigation_service import NavigationOperations
from .variable_service import VariableOperations
from .wait_service import WaitOperations


class PageOperations(Protocol):
    """页面操作协议"""

    def setup_page(self, page: Page) -> None:
        """设置页面对象"""
        ...

    def navigate_and_wait(self, url: str, wait_for: str = "networkidle") -> None:
        """导航到页面并等待加载完成"""
        ...

    def find_and_click(
        self, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> None:
        """查找元素并点击"""
        ...

    def find_and_fill(
        self, selector: str, value: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> None:
        """查找元素并填充内容"""
        ...

    def wait_and_assert_visible(
        self, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> None:
        """等待元素可见并断言"""
        ...

    def wait_and_assert_text(
        self,
        selector: str,
        expected_text: str,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> None:
        """等待元素并断言文本内容"""
        ...

    def capture_screenshot(self, name: str) -> str:
        """截图并返回路径"""
        ...

    def get_variable(self, name: str) -> Any:
        """获取变量值"""
        ...

    def set_variable(self, name: str, value: Any) -> None:
        """设置变量值"""
        ...


class PageService(BaseService):
    """页面服务实现

    整合多个基础服务，提供页面级别的复合操作。
    """

    def __init__(
        self,
        element_service: ElementOperations,
        navigation_service: NavigationOperations,
        wait_service: WaitOperations,
        assertion_service: AssertionOperations,
        variable_service: VariableOperations,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config)
        self.element_service = element_service
        self.navigation_service = navigation_service
        self.wait_service = wait_service
        self.assertion_service = assertion_service
        self.variable_service = variable_service

        # 配置选项
        self.auto_wait = self._config.get("auto_wait", True)
        self.screenshot_on_failure = self._config.get("screenshot_on_failure", True)

        self._page: Optional[Page] = None

    def setup_page(self, page: Page) -> None:
        """设置页面对象"""
        self._page = page

        # 为所有依赖服务设置页面对象
        if hasattr(self.element_service, "setup_page"):
            self.element_service.setup_page(page)
        if hasattr(self.navigation_service, "setup_page"):
            self.navigation_service.setup_page(page)
        if hasattr(self.wait_service, "setup_page"):
            self.wait_service.setup_page(page)
        if hasattr(self.assertion_service, "setup_page"):
            self.assertion_service.setup_page(page)
        if hasattr(self.variable_service, "setup_page"):
            self.variable_service.setup_page(page)

    def navigate_and_wait(self, url: str, wait_for: str = "networkidle") -> None:
        """导航到页面并等待加载完成"""
        try:
            self.navigation_service.goto(self._page, url)
            if self.auto_wait:
                self.wait_service.wait_for_timeout(3000)  # 等待3秒加载完成
        except Exception as e:
            if self.screenshot_on_failure:
                self.capture_screenshot(f"navigation_failure_{url.replace('/', '_')}")
            raise e

    def find_and_click(
        self, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> None:
        """查找元素并点击"""
        try:
            if self.auto_wait:
                self.wait_service.wait_for_element(
                    self._page, selector, "visible", timeout
                )
            self.element_service.click(self._page, selector)
        except Exception as e:
            if self.screenshot_on_failure:
                self.capture_screenshot(f"click_failure_{selector.replace(' ', '_')}")
            raise e

    def find_and_fill(
        self, selector: str, value: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> None:
        """查找元素并填充内容"""
        try:
            self.element_service.fill(self._page, selector, value, timeout)
        except Exception as e:
            if self.screenshot_on_failure:
                self.capture_screenshot(f"fill_failure_{selector.replace(' ', '_')}")
            raise e

    def wait_and_assert_visible(
        self, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ) -> None:
        """等待元素可见并断言"""
        self.assertion_service.assert_element_visible(self._page, selector)

    def wait_and_assert_text(
        self,
        selector: str,
        expected_text: str,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> None:
        """等待元素并断言文本内容"""
        self.assertion_service.assert_text(self._page, selector, expected_text)

    def capture_screenshot(self, name: str) -> str:
        """截图并返回路径"""
        if self._page:
            screenshot_path = f"evidence/screenshots/{name}.png"
            self._page.screenshot(path=screenshot_path)
            return screenshot_path
        return ""

    def get_variable(self, name: str) -> Any:
        """获取变量值"""
        return self.variable_service.get_variable(name)

    def set_variable(self, name: str, value: Any) -> None:
        """设置变量值"""
        self.variable_service.set_variable(name, value)

    def cleanup(self) -> None:
        """清理资源"""
        super().cleanup()
        self._page = None
