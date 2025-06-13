"""
等待操作混入类
包含各种等待方法
"""
import time
from typing import Optional, Literal
from config.constants import DEFAULT_TIMEOUT
from utils.logger import logger
from .decorators import handle_page_error


class WaitOperationsMixin:
    """等待操作混入类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @handle_page_error(description="等待指定时间")
    def wait_for_timeout(self, timeout: int):
        """等待指定时间"""
        self.page.wait_for_timeout(timeout)

    @handle_page_error(description="等待页面加载完成")
    def wait_for_load_state(
        self, state: Literal["domcontentloaded", "load", "networkidle"] | None = None
    ):
        """等待页面加载状态"""
        self.page.wait_for_load_state(state)

    @handle_page_error(description="等待元素消失")
    def wait_for_element_hidden(
        self, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ):
        """等待元素消失"""
        return self._locator(selector, state="hidden", timeout=timeout)

    @handle_page_error(description="等待元素可点击")
    def wait_for_element_clickable(
        self, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT
    ):
        """等待元素可点击"""
        locator = self._locator(selector, state="visible", timeout=timeout)
        is_enabled = not locator.is_disabled()
        if not is_enabled:
            raise TimeoutError(f"元素 {selector} 在 {timeout}ms 内未变为可点击状态")
        return locator

    @handle_page_error(description="等待元素包含文本")
    def wait_for_element_text(
        self,
        selector: str,
        expected: str,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ):
        """等待元素包含指定文本"""
        start_time = time.time()
        while time.time() - start_time < timeout / 1000:
            locator = self._locator(selector, timeout=timeout)
            actual_text = locator.inner_text()
            if expected in actual_text:
                return True
            time.sleep(0.1)
        raise TimeoutError(f"元素 {selector} 在 {timeout}ms 内未包含文本 '{expected}'")

    @handle_page_error(description="等待元素数量")
    def wait_for_element_count(
        self,
        selector: str,
        expected_count: int,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ):
        """等待元素数量达到预期值"""
        start_time = self.page.evaluate("() => Date.now()")
        while True:
            actual_count = self.get_element_count(selector)
            if actual_count == expected_count:
                return True

            current_time = self.page.evaluate("() => Date.now()")
            elapsed = (current_time - start_time) / 1000  # 转换为秒

            if elapsed > timeout / 1000:
                logger.error(
                    f"等待元素 {selector} 数量为 {expected_count} 超时，当前数量为 {actual_count}"
                )
                raise TimeoutError(f"等待元素 {selector} 数量为 {expected_count} 超时")

            self.page.wait_for_timeout(100)  # 等待100毫秒再检查

    @handle_page_error(description="等待网络请求完成")
    def wait_for_network_idle(self, timeout: Optional[int] = DEFAULT_TIMEOUT):
        """等待网络请求完成"""
        self.page.wait_for_load_state("networkidle", timeout=timeout)

    @handle_page_error(description="等待新窗口打开")
    def wait_for_new_window(self):
        """等待新窗口打开并返回新窗口"""
        with self.page.context.expect_page() as new_page_info:
            new_page = new_page_info.value
            new_page.wait_for_load_state()
            return new_page

    def get_element_count(self, selector: str) -> int:
        """获取元素数量 - 这个方法需要在主类中实现"""
        raise NotImplementedError("This method should be implemented in the main class")
