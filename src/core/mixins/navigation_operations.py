"""导航操作混入类"""
import allure
from typing import Optional
from utils.logger import logger
from .decorators import handle_page_error
from config.constants import DEFAULT_TIMEOUT


class NavigationOperationsMixin:
    """导航操作混入类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @handle_page_error(description="导航到指定URL")
    def navigate(self, url: str):
        """导航到指定URL"""
        resolved_url = self.variable_manager.replace_variables_refactored(url)
        with allure.step(f"导航到: {resolved_url}"):
            self.page.goto(resolved_url)
            logger.info(f"导航到: {resolved_url}")

    @handle_page_error(description="刷新页面")
    def refresh(self):
        """刷新页面"""
        with allure.step("刷新页面"):
            self.page.reload()
            logger.info("页面已刷新")

    @handle_page_error(description="后退")
    def go_back(self):
        """后退"""
        with allure.step("后退"):
            self.page.go_back()
            logger.info("页面后退")

    @handle_page_error(description="前进")
    def go_forward(self):
        """前进"""
        with allure.step("前进"):
            self.page.go_forward()
            logger.info("页面前进")

    @handle_page_error(description="等待页面加载")
    def wait_for_load_state(self, state: str = "load", timeout: Optional[int] = DEFAULT_TIMEOUT):
        """等待页面加载状态"""
        with allure.step(f"等待页面加载状态: {state}"):
            self.page.wait_for_load_state(state, timeout=timeout)
            logger.debug(f"页面加载状态达到: {state}")

    @handle_page_error(description="等待网络空闲")
    def wait_for_network_idle(self, timeout: Optional[int] = DEFAULT_TIMEOUT):
        """等待网络请求完成"""
        with allure.step("等待网络空闲"):
            self.page.wait_for_load_state("networkidle", timeout=timeout)
            logger.debug("网络请求已完成")

    @handle_page_error(description="获取当前URL")
    def get_current_url(self) -> str:
        """获取当前页面URL"""
        current_url = self.page.url
        logger.debug(f"当前URL: {current_url}")
        return current_url

    @handle_page_error(description="获取页面标题")
    def get_page_title(self) -> str:
        """获取页面标题"""
        title = self.page.title()
        logger.debug(f"页面标题: {title}")
        return title