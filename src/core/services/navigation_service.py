"""导航操作服务

提供页面导航相关的功能。
"""

import time
from typing import Protocol, Optional

from playwright.sync_api import Page

from config.constants import DEFAULT_TIMEOUT
from utils.logger import logger
from .base_service import BaseService


class NavigationOperations(Protocol):
    """导航操作协议"""
    
    def goto(self, page: Page, url: str, timeout: Optional[int] = None) -> None:
        """导航到指定URL"""
        ...
    
    def go_back(self, page: Page, timeout: Optional[int] = None) -> None:
        """后退"""
        ...
    
    def go_forward(self, page: Page, timeout: Optional[int] = None) -> None:
        """前进"""
        ...
    
    def reload(self, page: Page, timeout: Optional[int] = None) -> None:
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
    
    def goto(self, page: Page, url: str, timeout: Optional[int] = None) -> None:
        """导航到指定URL
        
        Args:
            page: Playwright页面对象
            url: 目标URL
            timeout: 超时时间（毫秒）
        """
        start_time = time.time()
        timeout = timeout or DEFAULT_TIMEOUT
        
        try:
            # 变量替换
            if self.variable_manager:
                resolved_url = self.variable_manager.replace_variables_refactored(url)
            else:
                resolved_url = url
            
            self._log_operation("goto", f"url: {resolved_url}")
            
            # 增加超时时间并使用更宽松的等待策略
            page.goto(resolved_url, timeout=timeout*2, wait_until='domcontentloaded')
            
            duration = time.time() - start_time
            self._record_operation("goto", duration, True)
            
            logger.info(f"成功导航到: {resolved_url}")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("goto", duration, False)
            logger.error(f"导航失败: {url}, 错误: {e}")
            raise
    
    def go_back(self, page: Page, timeout: Optional[int] = None) -> None:
        """后退到上一页
        
        Args:
            page: Playwright页面对象
            timeout: 超时时间（毫秒）
        """
        start_time = time.time()
        timeout = timeout or DEFAULT_TIMEOUT
        
        try:
            self._log_operation("go_back", "")
            
            page.go_back(timeout=timeout, wait_until='networkidle')
            
            duration = time.time() - start_time
            self._record_operation("go_back", duration, True)
            
            logger.debug("成功后退到上一页")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("go_back", duration, False)
            logger.error(f"后退失败: {e}")
            raise
    
    def go_forward(self, page: Page, timeout: Optional[int] = None) -> None:
        """前进到下一页
        
        Args:
            page: Playwright页面对象
            timeout: 超时时间（毫秒）
        """
        start_time = time.time()
        timeout = timeout or DEFAULT_TIMEOUT
        
        try:
            self._log_operation("go_forward", "")
            
            page.go_forward(timeout=timeout, wait_until='networkidle')
            
            duration = time.time() - start_time
            self._record_operation("go_forward", duration, True)
            
            logger.debug("成功前进到下一页")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("go_forward", duration, False)
            logger.error(f"前进失败: {e}")
            raise
    
    def reload(self, page: Page, timeout: Optional[int] = None) -> None:
        """刷新当前页面
        
        Args:
            page: Playwright页面对象
            timeout: 超时时间（毫秒）
        """
        start_time = time.time()
        timeout = timeout or DEFAULT_TIMEOUT
        
        try:
            self._log_operation("reload", "")
            
            page.reload(timeout=timeout, wait_until='networkidle')
            
            duration = time.time() - start_time
            self._record_operation("reload", duration, True)
            
            logger.debug("成功刷新页面")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("reload", duration, False)
            logger.error(f"刷新页面失败: {e}")
            raise
    
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
    
    def wait_for_load_state(self, page: Page, state: str = 'networkidle', timeout: Optional[int] = None) -> None:
        """等待页面加载状态
        
        Args:
            page: Playwright页面对象
            state: 等待的状态 ('load', 'domcontentloaded', 'networkidle')
            timeout: 超时时间（毫秒）
        """
        start_time = time.time()
        timeout = timeout or DEFAULT_TIMEOUT
        
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
    # ==================== 从Mixin迁移的方法 ====================
    def navigate(self, page: Page, url: str):
        """导航到指定URL"""
        if self.variable_manager:
            resolved_url = self.variable_manager.replace_variables_refactored(url)
        else:
            resolved_url = url
        with allure.step(f"导航到: {resolved_url}"):
            page.goto(resolved_url)
            logger.info(f"导航到: {resolved_url}")

    def refresh(self, page: Page):
        """刷新页面"""
        with allure.step("刷新页面"):
            page.reload()
            logger.info("页面已刷新")

    def go_back(self, page: Page):
        """后退"""
        with allure.step("后退"):
            page.go_back()
            logger.info("页面后退")

    def go_forward(self, page: Page):
        """前进"""
        with allure.step("前进"):
            page.go_forward()
            logger.info("页面前进")
