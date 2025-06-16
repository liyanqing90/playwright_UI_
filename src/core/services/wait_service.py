"""等待操作服务

提供各种等待操作的功能。
"""

import time
from typing import Protocol, Optional, Any

from playwright.sync_api import Page

from config.constants import DEFAULT_TIMEOUT
from utils.logger import logger
from .base_service import BaseService


class WaitOperations(Protocol):
    """等待操作协议"""
    
    def wait_for_element(self, page: Page, selector: str, state: str = 'visible', timeout: Optional[int] = None) -> None:
        """等待元素状态"""
        ...
    
    def wait_for_text(self, page: Page, selector: str, text: str, timeout: Optional[int] = None) -> None:
        """等待元素包含指定文本"""
        ...
    
    def wait_for_url(self, page: Page, url_pattern: str, timeout: Optional[int] = None) -> None:
        """等待URL匹配"""
        ...
    
    def wait_for_function(self, page: Page, expression: str, timeout: Optional[int] = None) -> Any:
        """等待JavaScript表达式返回真值"""
        ...
    
    def wait_for_timeout(self, page: Page, timeout: int) -> None:
        """等待指定时间（毫秒）"""
        ...
    
    def sleep(self, seconds: float) -> None:
        """休眠指定时间"""
        ...

class WaitService(BaseService):
    """等待操作服务实现"""
    
    def __init__(self, performance_manager=None):
        super().__init__(performance_manager)
    
    def wait_for_element(self, page: Page, selector: str, state: str = 'visible', timeout: Optional[int] = None) -> None:
        """等待元素达到指定状态
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            state: 等待的状态 ('attached', 'detached', 'visible', 'hidden')
            timeout: 超时时间（毫秒）
        """
        start_time = time.time()
        timeout = timeout or DEFAULT_TIMEOUT
        
        try:
            self._log_operation("wait_for_element", f"selector: {selector}, state: {state}")
            
            locator = self._get_locator(page, selector)
            locator.first.wait_for(state=state, timeout=timeout)
            
            duration = time.time() - start_time
            self._record_operation("wait_for_element", duration, True)
            
            logger.debug(f"元素状态达到: {selector} -> {state}")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("wait_for_element", duration, False)
            logger.error(f"等待元素状态失败: {selector} -> {state}, 错误: {e}")
            raise
    
    def wait_for_text(self, page: Page, selector: str, text: str, timeout: Optional[int] = None) -> None:
        """等待元素包含指定文本
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            text: 期望的文本内容
            timeout: 超时时间（毫秒）
        """
        start_time = time.time()
        timeout = timeout or DEFAULT_TIMEOUT
        
        try:
            self._log_operation("wait_for_text", f"selector: {selector}, text: {text}")
            
            locator = self._get_locator(page, selector)
            
            # 等待元素包含指定文本
            def check_text():
                try:
                    element_text = locator.first.text_content(timeout=1000)
                    return text in (element_text or "")
                except:
                    return False
            
            page.wait_for_function(
                lambda: check_text(),
                timeout=timeout
            )
            
            duration = time.time() - start_time
            self._record_operation("wait_for_text", duration, True)
            
            logger.debug(f"元素文本匹配: {selector} 包含 '{text}'")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("wait_for_text", duration, False)
            logger.error(f"等待文本失败: {selector} 包含 '{text}', 错误: {e}")
            raise
    
    def wait_for_url(self, page: Page, url_pattern: str, timeout: Optional[int] = None) -> None:
        """等待URL匹配指定模式
        
        Args:
            page: Playwright页面对象
            url_pattern: URL模式（支持正则表达式）
            timeout: 超时时间（毫秒）
        """
        start_time = time.time()
        timeout = timeout or DEFAULT_TIMEOUT
        
        try:
            self._log_operation("wait_for_url", f"pattern: {url_pattern}")
            
            import re
            pattern = re.compile(url_pattern)
            
            page.wait_for_function(
                f"() => {{'return /{url_pattern}/.test(window.location.href)'}}",
                timeout=timeout
            )
            
            duration = time.time() - start_time
            self._record_operation("wait_for_url", duration, True)
            
            current_url = page.url
            logger.debug(f"URL匹配成功: {current_url} 匹配 {url_pattern}")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("wait_for_url", duration, False)
            logger.error(f"等待URL匹配失败: {url_pattern}, 错误: {e}")
            raise
    
    def wait_for_function(self, page: Page, expression: str, timeout: Optional[int] = None) -> Any:
        """等待JavaScript表达式返回真值
        
        Args:
            page: Playwright页面对象
            expression: JavaScript表达式
            timeout: 超时时间（毫秒）
            
        Returns:
            Any: 表达式的返回值
        """
        start_time = time.time()
        timeout = timeout or DEFAULT_TIMEOUT
        
        try:
            self._log_operation("wait_for_function", f"expression: {expression[:100]}...")
            
            result = page.wait_for_function(expression, timeout=timeout)
            
            duration = time.time() - start_time
            self._record_operation("wait_for_function", duration, True)
            
            logger.debug(f"JavaScript表达式执行成功: {expression[:50]}...")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("wait_for_function", duration, False)
            logger.error(f"等待JavaScript表达式失败: {expression[:50]}..., 错误: {e}")
            raise
    
    def sleep(self, seconds: float) -> None:
        """休眠指定时间
        
        Args:
            seconds: 休眠时间（秒）
        """
        try:
            self._log_operation("sleep", f"duration: {seconds}s")
            
            time.sleep(seconds)
            
            self._record_operation("sleep", seconds, True)
            logger.debug(f"休眠完成: {seconds}秒")
            
        except Exception as e:
            logger.error(f"休眠失败: {e}")
            raise
    
    def wait_for_selector_count(self, page: Page, selector: str, count: int, timeout: Optional[int] = None) -> None:
        """等待选择器匹配指定数量的元素
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            count: 期望的元素数量
            timeout: 超时时间（毫秒）
        """
        start_time = time.time()
        timeout = timeout or DEFAULT_TIMEOUT
        
        try:
            self._log_operation("wait_for_selector_count", f"selector: {selector}, count: {count}")
            
            page.wait_for_function(
                f"() => document.querySelectorAll('{selector}').length === {count}",
                timeout=timeout
            )
            
            duration = time.time() - start_time
            self._record_operation("wait_for_selector_count", duration, True)
            
            logger.debug(f"元素数量匹配: {selector} 数量为 {count}")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("wait_for_selector_count", duration, False)
            logger.error(f"等待元素数量失败: {selector} 期望 {count}, 错误: {e}")
            raise
    
    def wait_for_network_idle(self, page: Page, timeout: Optional[int] = None) -> None:
        """等待网络空闲
        
        Args:
            page: Playwright页面对象
            timeout: 超时时间（毫秒）
        """
        start_time = time.time()
        timeout = timeout or DEFAULT_TIMEOUT
        
        try:
            self._log_operation("wait_for_network_idle", "")
            
            page.wait_for_load_state('networkidle', timeout=timeout)
            
            duration = time.time() - start_time
            self._record_operation("wait_for_network_idle", duration, True)
            
            logger.debug("网络空闲状态达到")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("wait_for_network_idle", duration, False)
            logger.error(f"等待网络空闲失败: {e}")
            raise
    
    def wait_for_timeout(self, page: Page, timeout: int) -> None:
        """等待指定时间
        
        Args:
            page: Playwright页面对象
            timeout: 等待时间（毫秒）
        """
        start_time = time.time()
        
        try:
            self._log_operation("wait_for_timeout", f"timeout: {timeout}ms")
            
            page.wait_for_timeout(timeout)
            
            duration = time.time() - start_time
            self._record_operation("wait_for_timeout", duration, True)
            
            logger.debug(f"等待完成: {timeout}ms")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("wait_for_timeout", duration, False)
            logger.error(f"等待超时失败: {e}")
            raise