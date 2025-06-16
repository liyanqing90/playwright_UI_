"""元素操作服务

提供页面元素操作的核心功能。
"""

import time
from typing import Protocol, Any, Optional

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from config.constants import DEFAULT_TIMEOUT
from utils.logger import logger
from .base_service import BaseService


class ElementOperations(Protocol):
    """元素操作协议
    
    定义元素操作的标准接口。
    """
    
    def click(self, page: Page, selector: str, timeout: Optional[int] = None) -> None:
        """点击元素"""
        ...
    
    def fill(self, page: Page, selector: str, value: str, timeout: Optional[int] = None) -> None:
        """填写文本"""
        ...
    
    def double_click(self, page: Page, selector: str, timeout: Optional[int] = None) -> None:
        """双击元素"""
        ...
    
    def hover(self, page: Page, selector: str, timeout: Optional[int] = None) -> None:
        """悬停元素"""
        ...
    
    def get_text(self, page: Page, selector: str, timeout: Optional[int] = None) -> str:
        """获取元素文本"""
        ...
    
    def get_attribute(self, page: Page, selector: str, attribute: str, timeout: Optional[int] = None) -> Optional[str]:
        """获取元素属性"""
        ...
    
    def is_visible(self, page: Page, selector: str, timeout: Optional[int] = None) -> bool:
        """检查元素是否可见"""
        ...
    
    def is_enabled(self, page: Page, selector: str, timeout: Optional[int] = None) -> bool:
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
        super().__init__(performance_manager)
        self.variable_manager = variable_manager
    
    def click(self, page: Page, selector: str, timeout: Optional[int] = None) -> None:
        """点击指定的元素
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            timeout: 超时时间（毫秒），默认使用DEFAULT_TIMEOUT
            
        Raises:
            PlaywrightTimeoutError: 如果元素超时未出现
        """
        start_time = time.time()
        timeout = timeout or DEFAULT_TIMEOUT
        
        try:
            self._log_operation("click", f"selector: {selector}")
            
            locator = self._get_locator(page, selector)
            # 先滚动到元素位置，确保元素在视口内
            # locator.first.scroll_into_view_if_needed(timeout=timeout)
            locator.first.click(timeout=timeout, force=True)
            
            duration = time.time() - start_time
            self._record_operation("click", duration, True)
            
            logger.debug(f"成功点击元素: {selector}")
            
        except PlaywrightTimeoutError as e:
            duration = time.time() - start_time
            self._record_operation("click", duration, False)
            logger.error(f"点击元素超时: {selector}, 超时时间: {timeout}ms")
            raise
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("click", duration, False)
            logger.error(f"点击元素失败: {selector}, 错误: {e}")
            raise
    
    def fill(self, page: Page, selector: str, value: str, timeout: Optional[int] = None) -> None:
        """在输入框中填写文本
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            value: 要填写的文本
            timeout: 超时时间（毫秒）
        """
        start_time = time.time()
        timeout = timeout or DEFAULT_TIMEOUT
        
        try:
            # 变量替换
            if self.variable_manager:
                resolved_value = self.variable_manager.replace_variables_refactored(value)
            else:
                resolved_value = value
            
            if resolved_value is not None:
                resolved_value = str(resolved_value)
            
            self._log_operation("fill", f"selector: {selector}, value: {resolved_value}")
            
            locator = self._get_locator(page, selector)
            locator.first.fill(resolved_value, timeout=timeout)
            
            duration = time.time() - start_time
            self._record_operation("fill", duration, True)
            
            logger.debug(f"成功填写文本: {selector} = {resolved_value}")
            
        except PlaywrightTimeoutError as e:
            duration = time.time() - start_time
            self._record_operation("fill", duration, False)
            logger.error(f"填写文本超时: {selector}")
            raise
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("fill", duration, False)
            logger.error(f"填写文本失败: {selector}, 错误: {e}")
            raise
    
    def double_click(self, page: Page, selector: str, timeout: Optional[int] = None) -> None:
        """双击元素
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            timeout: 超时时间（毫秒）
        """
        start_time = time.time()
        timeout = timeout or DEFAULT_TIMEOUT
        
        try:
            self._log_operation("double_click", f"selector: {selector}")
            
            locator = self._get_locator(page, selector)
            locator.first.dblclick(timeout=timeout)
            
            duration = time.time() - start_time
            self._record_operation("double_click", duration, True)
            
            logger.debug(f"成功双击元素: {selector}")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("double_click", duration, False)
            logger.error(f"双击元素失败: {selector}, 错误: {e}")
            raise
    
    def hover(self, page: Page, selector: str, timeout: Optional[int] = None) -> None:
        """悬停在元素上
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            timeout: 超时时间（毫秒）
        """
        start_time = time.time()
        timeout = timeout or DEFAULT_TIMEOUT
        
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
    
    def get_text(self, page: Page, selector: str, timeout: Optional[int] = None) -> str:
        """获取元素文本内容
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            timeout: 超时时间（毫秒）
            
        Returns:
            str: 元素的文本内容
        """
        start_time = time.time()
        timeout = timeout or DEFAULT_TIMEOUT
        
        try:
            self._log_operation("get_text", f"selector: {selector}")
            
            locator = self._get_locator(page, selector)
            # 先确保元素可见
            locator.first.wait_for(state='visible', timeout=timeout)
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
    
    def get_attribute(self, page: Page, selector: str, attribute: str, timeout: Optional[int] = None) -> Optional[str]:
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
        timeout = timeout or DEFAULT_TIMEOUT
        
        try:
            self._log_operation("get_attribute", f"selector: {selector}, attribute: {attribute}")
            
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
    
    def is_visible(self, page: Page, selector: str, timeout: Optional[int] = None) -> bool:
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
    
    def is_enabled(self, page: Page, selector: str, timeout: Optional[int] = None) -> bool:
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
    
    def wait_and_click(self, page: Page, selector: str, timeout: Optional[int] = None) -> None:
        """等待元素可点击并点击
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            timeout: 超时时间（毫秒）
        """
        timeout = timeout or DEFAULT_TIMEOUT
        
        # 先等待元素可见
        locator = self._get_locator(page, selector)
        locator.first.wait_for(state='visible', timeout=timeout)
        
        # 然后点击
        self.click(page, selector, timeout)
    
    def wait_and_fill(self, page: Page, selector: str, value: str, timeout: Optional[int] = None) -> None:
        """等待元素可见并填写文本
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            value: 要填写的文本
            timeout: 超时时间（毫秒）
        """
        timeout = timeout or DEFAULT_TIMEOUT
        
        # 先等待元素可见
        locator = self._get_locator(page, selector)
        locator.first.wait_for(state='visible', timeout=timeout)
        
        # 然后填写
        self.fill(page, selector, value, timeout)
    # ==================== 从Mixin迁移的方法 ====================
    def click(self, page: Page, selector: str):
        """点击元素"""
        page.locator(selector).first.click(timeout=DEFAULT_TIMEOUT, force=True)

    def fill(self, page: Page, selector: str, value: Any):
        """在输入框中填写文本"""
        if self.variable_manager:
            resolved_text = self.variable_manager.replace_variables_refactored(value)
        else:
            resolved_text = value
        if resolved_text is not None:
            resolved_text = str(resolved_text)
        page.locator(selector).first.fill(resolved_text)

    def get_text(self, page: Page, selector: str) -> str:
        """获取元素文本"""
        return page.locator(selector).first.inner_text()

    def hover(self, page: Page, selector: str):
        """鼠标悬停在元素上"""
        page.locator(selector).first.hover()

    def double_click(self, page: Page, selector: str):
        """双击元素"""
        page.locator(selector).first.dblclick()
