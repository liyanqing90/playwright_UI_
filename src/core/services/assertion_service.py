"""核心断言服务

提供基础、稳定的断言功能。
高级断言功能请使用assertion_commands插件。"""

import time
from typing import Protocol, Optional

from playwright.sync_api import Page

from utils.logger import logger
from .base_service import BaseService


class AssertionOperations(Protocol):
    """断言操作协议"""
    
    def assert_element_visible(self, page: Page, selector: str, message: Optional[str] = None) -> None:
        """断言元素可见"""
        ...
    
    def assert_element_hidden(self, page: Page, selector: str, message: Optional[str] = None) -> None:
        """断言元素隐藏"""
        ...
    
    def assert_text_contains(self, page: Page, selector: str, text: str, message: Optional[str] = None) -> None:
        """断言元素包含指定文本"""
        ...
    
    def assert_text_equals(self, page: Page, selector: str, text: str, message: Optional[str] = None) -> None:
        """断言元素文本等于指定值"""
        ...
    
    def assert_url_contains(self, page: Page, url_part: str, message: Optional[str] = None) -> None:
        """断言URL包含指定部分"""
        ...
    
    def assert_url(self, page: Page, expected: str, message: Optional[str] = None) -> None:
        """断言URL等于指定值"""
        ...
    
    def assert_title_contains(self, page: Page, title_part: str, message: Optional[str] = None) -> None:
        """断言页面标题包含指定文本"""
        ...
    
    def assert_attribute(self, page: Page, selector: str, attribute: str, expected: str, message: Optional[str] = None) -> None:
        """断言元素属性值"""
        ...
    
    def assert_value(self, page: Page, selector: str, expected: str, message: Optional[str] = None) -> None:
        """断言元素值等于指定值"""
        ...
    
    def assert_exists(self, page: Page, selector: str, message: Optional[str] = None) -> None:
        """断言元素存在"""
        ...
    
    def assert_not_exists(self, page: Page, selector: str, message: Optional[str] = None) -> None:
        """断言元素不存在"""
        ...
    
    def assert_element_enabled(self, page: Page, selector: str, message: Optional[str] = None) -> None:
        """断言元素启用"""
        ...
    
    def assert_element_disabled(self, page: Page, selector: str, message: Optional[str] = None) -> None:
        """断言元素禁用"""
        ...
    
    def assert_values(self, page: Page, selector: str, expected: list, message: Optional[str] = None) -> None:
        """断言元素多个值"""
        ...

class AssertionService(BaseService):
    """核心断言服务
    
    提供基础、稳定的断言功能。
    专注于最常用的断言操作，保证高性能和稳定性。
    
    高级断言功能（软断言、批量断言、重试断言等）
    请使用assertion_commands插件。
    """
    
    def __init__(self, performance_manager=None):
        super().__init__(performance_manager)
    
    def get_service_name(self) -> str:
        return "assertion_service"
    
    def _do_initialize(self) -> bool:
        """初始化断言服务"""
        try:
            logger.info("断言服务初始化成功")
            return True
        except Exception as e:
            logger.error(f"断言服务初始化失败: {e}")
            return False
    
    def _do_cleanup(self):
        """清理断言服务"""
        logger.info("断言服务清理完成")
    
    def assert_element_visible(self, page: Page, selector: str, message: Optional[str] = None) -> None:
        """断言元素可见
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            message: 自定义错误消息
            
        Raises:
            AssertionError: 当元素不可见时
        """
        start_time = time.time()
        
        try:
            self._log_operation("assert_element_visible", f"selector: {selector}")
            
            locator = self._get_locator(page, selector)
            
            # 检查元素是否可见
            is_visible = locator.first.is_visible()
            
            duration = time.time() - start_time
            
            if not is_visible:
                error_msg = message or f"元素不可见: {selector}"
                self._record_operation("assert_element_visible", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            self._record_operation("assert_element_visible", duration, True)
            logger.debug(f"断言成功: 元素可见 {selector}")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("assert_element_visible", duration, False)
            if isinstance(e, AssertionError):
                raise
            error_msg = message or f"断言元素可见失败: {selector}, 错误: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg) from e
    
    def assert_element_hidden(self, page: Page, selector: str, message: Optional[str] = None) -> None:
        """断言元素隐藏
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            message: 自定义错误消息
            
        Raises:
            AssertionError: 当元素可见时
        """
        start_time = time.time()
        
        try:
            self._log_operation("assert_element_hidden", f"selector: {selector}")
            
            locator = self._get_locator(page, selector)
            
            # 检查元素是否隐藏
            is_visible = locator.first.is_visible()
            
            duration = time.time() - start_time
            
            if is_visible:
                error_msg = message or f"元素应该隐藏但实际可见: {selector}"
                self._record_operation("assert_element_hidden", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            self._record_operation("assert_element_hidden", duration, True)
            logger.debug(f"断言成功: 元素隐藏 {selector}")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("assert_element_hidden", duration, False)
            if isinstance(e, AssertionError):
                raise
            error_msg = message or f"断言元素隐藏失败: {selector}, 错误: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg) from e
    
    def assert_text_contains(self, page: Page, selector: str, text: str, message: Optional[str] = None) -> None:
        """断言元素包含指定文本
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            text: 期望包含的文本
            message: 自定义错误消息
            
        Raises:
            AssertionError: 当元素不包含指定文本时
        """
        start_time = time.time()
        
        try:
            self._log_operation("assert_text_contains", f"selector: {selector}, text: {text}")
            
            locator = self._get_locator(page, selector)
            
            # 获取元素文本
            element_text = locator.first.text_content() or ""
            
            duration = time.time() - start_time
            
            if text not in element_text:
                error_msg = message or f"元素文本不包含期望内容: {selector}, 实际: '{element_text}', 期望包含: '{text}'"
                self._record_operation("assert_text_contains", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            self._record_operation("assert_text_contains", duration, True)
            logger.debug(f"断言成功: 元素包含文本 {selector} 包含 '{text}'")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("assert_text_contains", duration, False)
            if isinstance(e, AssertionError):
                raise
            error_msg = message or f"断言文本包含失败: {selector}, 错误: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg) from e
    
    def assert_text_equals(self, page: Page, selector: str, text: str, message: Optional[str] = None) -> None:
        """断言元素文本等于指定值
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            text: 期望的文本
            message: 自定义错误消息
            
        Raises:
            AssertionError: 当元素文本不等于指定值时
        """
        start_time = time.time()
        
        try:
            self._log_operation("assert_text_equals", f"selector: {selector}, text: {text}")
            
            locator = self._get_locator(page, selector)
            
            # 获取元素文本
            element_text = (locator.first.text_content() or "").strip()
            
            duration = time.time() - start_time
            
            # 记录调试信息
            logger.debug(f"断言文本比较: 选择器={selector}, 实际='{element_text}', 期望='{text}'")
            
            if element_text != text:
                error_msg = message or f"元素文本不等于期望值: {selector}, 实际: '{element_text}', 期望: '{text}'"
                self._record_operation("assert_text_equals", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            self._record_operation("assert_text_equals", duration, True)
            logger.debug(f"断言成功: 元素文本等于 {selector} = '{text}'")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("assert_text_equals", duration, False)
            if isinstance(e, AssertionError):
                raise
            error_msg = message or f"断言文本相等失败: {selector}, 错误: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg) from e
    
    def assert_url_contains(self, page: Page, url_part: str, message: Optional[str] = None) -> None:
        """断言URL包含指定部分
        
        Args:
            page: Playwright页面对象
            url_part: 期望包含的URL部分
            message: 自定义错误消息
            
        Raises:
            AssertionError: 当URL不包含指定部分时
        """
        start_time = time.time()
        
        try:
            self._log_operation("assert_url_contains", f"url_part: {url_part}")
            
            current_url = page.url
            
            duration = time.time() - start_time
            
            if url_part not in current_url:
                error_msg = message or f"URL不包含期望部分: 实际: '{current_url}', 期望包含: '{url_part}'"
                self._record_operation("assert_url_contains", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            self._record_operation("assert_url_contains", duration, True)
            logger.debug(f"断言成功: URL包含 '{url_part}'")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("assert_url_contains", duration, False)
            if isinstance(e, AssertionError):
                raise
            error_msg = message or f"断言URL包含失败: {url_part}, 错误: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg) from e
    
    def assert_title_contains(self, page: Page, title_part: str, message: Optional[str] = None) -> None:
        """断言页面标题包含指定文本
        
        Args:
            page: Playwright页面对象
            title_part: 期望包含的标题部分
            message: 自定义错误消息
            
        Raises:
            AssertionError: 当标题不包含指定文本时
        """
        start_time = time.time()
        
        try:
            self._log_operation("assert_title_contains", f"title_part: {title_part}")
            
            current_title = page.title()
            
            duration = time.time() - start_time
            
            if title_part not in current_title:
                error_msg = message or f"页面标题不包含期望文本: 实际: '{current_title}', 期望包含: '{title_part}'"
                self._record_operation("assert_title_contains", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            self._record_operation("assert_title_contains", duration, True)
            logger.debug(f"断言成功: 标题包含 '{title_part}'")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("assert_title_contains", duration, False)
            if isinstance(e, AssertionError):
                raise
            error_msg = message or f"断言标题包含失败: {title_part}, 错误: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg) from e
    
    def assert_title(self, page: Page, expected_title: str, message: Optional[str] = None) -> None:
        """断言页面标题等于指定值
        
        Args:
            page: Playwright页面对象
            expected_title: 期望的标题
            message: 自定义错误消息
            
        Raises:
            AssertionError: 当标题不等于期望值时
        """
        start_time = time.time()
        
        try:
            self._log_operation("assert_title", f"expected_title: {expected_title}")
            
            current_title = page.title()
            
            duration = time.time() - start_time
            
            if current_title != expected_title:
                error_msg = message or f"页面标题不等于期望值: 实际: '{current_title}', 期望: '{expected_title}'"
                self._record_operation("assert_title", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            self._record_operation("assert_title", duration, True)
            logger.debug(f"断言成功: 页面标题 = '{expected_title}'")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("assert_title", duration, False)
            if isinstance(e, AssertionError):
                raise
            error_msg = message or f"断言页面标题失败: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg) from e
    
    def assert_attribute_equals(self, page: Page, selector: str, attribute: str, value: str, message: Optional[str] = None) -> None:
        """断言元素属性等于指定值
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            attribute: 属性名
            value: 期望的属性值
            message: 自定义错误消息
            
        Raises:
            AssertionError: 当属性值不等于期望值时
        """
        start_time = time.time()
        
        try:
            self._log_operation("assert_attribute_equals", f"selector: {selector}, attribute: {attribute}, value: {value}")
            
            locator = self._get_locator(page, selector)
            
            # 获取属性值
            actual_value = locator.first.get_attribute(attribute)
            
            duration = time.time() - start_time
            
            if actual_value != value:
                error_msg = message or f"元素属性不等于期望值: {selector}[{attribute}], 实际: '{actual_value}', 期望: '{value}'"
                self._record_operation("assert_attribute_equals", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            self._record_operation("assert_attribute_equals", duration, True)
            logger.debug(f"断言成功: 属性值相等 {selector}[{attribute}] = '{value}'")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("assert_attribute_equals", duration, False)
            if isinstance(e, AssertionError):
                raise
            error_msg = message or f"断言属性值相等失败: {selector}[{attribute}], 错误: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg) from e
    
    def assert_attribute(self, page: Page, selector: str, attribute: str, expected: str, message: Optional[str] = None) -> None:
        """断言元素属性值
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            attribute: 属性名
            expected: 期望的属性值
            message: 自定义错误消息
            
        Raises:
            AssertionError: 当属性值不等于期望值时
        """
        # 直接调用 assert_attribute_equals 方法
        self.assert_attribute_equals(page, selector, attribute, expected, message)
    
    def assert_element_count(self, page: Page, selector: str, count: int, message: Optional[str] = None) -> None:
        """断言元素数量等于指定值
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            count: 期望的元素数量
            message: 自定义错误消息
            
        Raises:
            AssertionError: 当元素数量不等于期望值时
        """
        start_time = time.time()
        
        try:
            self._log_operation("assert_element_count", f"selector: {selector}, count: {count}")
            
            locator = self._get_locator(page, selector)
            
            # 获取元素数量
            actual_count = locator.count()
            
            duration = time.time() - start_time
            
            if actual_count != count:
                error_msg = message or f"元素数量不等于期望值: {selector}, 实际: {actual_count}, 期望: {count}"
                self._record_operation("assert_element_count", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            self._record_operation("assert_element_count", duration, True)
            logger.debug(f"断言成功: 元素数量 {selector} = {count}")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("assert_element_count", duration, False)
            if isinstance(e, AssertionError):
                raise
            error_msg = message or f"断言元素数量失败: {selector}, 错误: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg) from e
    
    def assert_url(self, page: Page, expected: str, message: Optional[str] = None) -> None:
        """断言URL等于指定值
        
        Args:
            page: Playwright页面对象
            expected: 期望的URL
            message: 自定义错误消息
            
        Raises:
            AssertionError: 当URL不等于期望值时
        """
        start_time = time.time()
        
        try:
            self._log_operation("assert_url", f"expected: {expected}")
            
            current_url = page.url
            
            duration = time.time() - start_time
            
            if current_url != expected:
                error_msg = message or f"URL不等于期望值: 实际: '{current_url}', 期望: '{expected}'"
                self._record_operation("assert_url", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            self._record_operation("assert_url", duration, True)
            logger.debug(f"断言成功: URL等于 '{expected}'")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("assert_url", duration, False)
            if isinstance(e, AssertionError):
                raise
            error_msg = message or f"断言URL失败: {expected}, 错误: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg) from e
    
    def assert_value(self, page: Page, selector: str, expected: str, message: Optional[str] = None) -> None:
        """断言元素值等于指定值
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            expected: 期望的值
            message: 自定义错误消息
            
        Raises:
            AssertionError: 当元素值不等于期望值时
        """
        start_time = time.time()
        
        try:
            self._log_operation("assert_value", f"selector: {selector}, expected: {expected}")
            
            element = page.locator(selector)
            if not element.is_visible():
                error_msg = message or f"元素不可见: {selector}"
                duration = time.time() - start_time
                self._record_operation("assert_value", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            # 获取元素的值
            actual_value = element.input_value() if element.get_attribute("value") is not None else element.text_content()
            
            duration = time.time() - start_time
            
            if actual_value != expected:
                error_msg = message or f"元素值不等于期望值: 实际: '{actual_value}', 期望: '{expected}'"
                self._record_operation("assert_value", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            self._record_operation("assert_value", duration, True)
            logger.debug(f"断言成功: 元素 {selector} 的值等于 '{expected}'")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("assert_value", duration, False)
            if isinstance(e, AssertionError):
                raise
            error_msg = message or f"断言元素值失败: {selector}, 期望: {expected}, 错误: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg) from e
    
    def assert_exists(self, page: Page, selector: str, message: Optional[str] = None) -> None:
        """断言元素存在"""
        start_time = time.time()
        
        try:
            self._log_operation("assert_exists", f"selector: {selector}")
            
            element = page.locator(selector)
            count = element.count()
            
            duration = time.time() - start_time
            
            if count == 0:
                error_msg = message or f"元素不存在: {selector}"
                self._record_operation("assert_exists", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            self._record_operation("assert_exists", duration, True)
            logger.debug(f"断言成功: 元素 {selector} 存在")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("assert_exists", duration, False)
            if isinstance(e, AssertionError):
                raise
            error_msg = message or f"断言元素存在失败: {selector}, 错误: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg) from e
    
    def assert_not_exists(self, page: Page, selector: str, message: Optional[str] = None) -> None:
        """断言元素不存在"""
        start_time = time.time()
        
        try:
            self._log_operation("assert_not_exists", f"selector: {selector}")
            
            element = page.locator(selector)
            count = element.count()
            
            duration = time.time() - start_time
            
            if count > 0:
                error_msg = message or f"元素存在但期望不存在: {selector}"
                self._record_operation("assert_not_exists", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            self._record_operation("assert_not_exists", duration, True)
            logger.debug(f"断言成功: 元素 {selector} 不存在")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("assert_not_exists", duration, False)
            if isinstance(e, AssertionError):
                raise
            error_msg = message or f"断言元素不存在失败: {selector}, 错误: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg) from e
    
    def assert_element_enabled(self, page: Page, selector: str, message: Optional[str] = None) -> None:
        """断言元素启用"""
        start_time = time.time()
        
        try:
            self._log_operation("assert_element_enabled", f"selector: {selector}")
            
            element = page.locator(selector)
            if not element.is_visible():
                error_msg = message or f"元素不可见: {selector}"
                duration = time.time() - start_time
                self._record_operation("assert_element_enabled", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            is_enabled = element.is_enabled()
            
            duration = time.time() - start_time
            
            if not is_enabled:
                error_msg = message or f"元素未启用: {selector}"
                self._record_operation("assert_element_enabled", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            self._record_operation("assert_element_enabled", duration, True)
            logger.debug(f"断言成功: 元素 {selector} 已启用")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("assert_element_enabled", duration, False)
            if isinstance(e, AssertionError):
                raise
            error_msg = message or f"断言元素启用失败: {selector}, 错误: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg) from e
    
    def assert_element_disabled(self, page: Page, selector: str, message: Optional[str] = None) -> None:
        """断言元素禁用"""
        start_time = time.time()
        
        try:
            self._log_operation("assert_element_disabled", f"selector: {selector}")
            
            element = page.locator(selector)
            if not element.is_visible():
                error_msg = message or f"元素不可见: {selector}"
                duration = time.time() - start_time
                self._record_operation("assert_element_disabled", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            is_enabled = element.is_enabled()
            
            duration = time.time() - start_time
            
            if is_enabled:
                error_msg = message or f"元素已启用但期望禁用: {selector}"
                self._record_operation("assert_element_disabled", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            self._record_operation("assert_element_disabled", duration, True)
            logger.debug(f"断言成功: 元素 {selector} 已禁用")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("assert_element_disabled", duration, False)
            if isinstance(e, AssertionError):
                raise
            error_msg = message or f"断言元素禁用失败: {selector}, 错误: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg) from e
    
    def assert_values(self, page: Page, selector: str, expected: list, message: Optional[str] = None) -> None:
        """断言元素多个值"""
        start_time = time.time()
        
        try:
            self._log_operation("assert_values", f"selector: {selector}, expected: {expected}")
            
            elements = page.locator(selector)
            count = elements.count()
            
            if count == 0:
                error_msg = message or f"未找到元素: {selector}"
                duration = time.time() - start_time
                self._record_operation("assert_values", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            # 获取所有元素的值
            actual_values = []
            for i in range(count):
                element = elements.nth(i)
                value = element.input_value() if element.get_attribute("value") is not None else element.text_content()
                actual_values.append(value)
            
            duration = time.time() - start_time
            
            if actual_values != expected:
                error_msg = message or f"元素值不匹配: 实际: {actual_values}, 期望: {expected}"
                self._record_operation("assert_values", duration, False)
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            self._record_operation("assert_values", duration, True)
            logger.debug(f"断言成功: 元素 {selector} 的值匹配 {expected}")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("assert_values", duration, False)
            if isinstance(e, AssertionError):
                raise
            error_msg = message or f"断言元素多个值失败: {selector}, 期望: {expected}, 错误: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg) from e
    # ==================== 从Mixin迁移的方法 ====================
    def assert_text(self, page: Page, selector: str, expected: str):
        """断言元素文本（软断言）"""
        if self.variable_manager:
            resolved_expected = self.variable_manager.replace_variables_refactored(expected)
        else:
            resolved_expected = expected
        try:
            actual_text = page.locator(selector).first.inner_text()
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
            assertion_manager.soft_assert(
                condition=False,
                message=f"获取元素文本失败: {str(e)}",
                expected=resolved_expected,
                actual="无法获取",
                step_description=f"断言元素 {selector} 的文本"
            )

        expect(page.locator(selector).first).to_have_text(resolved_expected)

    def assert_visible(self, page: Page, selector: str):
        """断言元素可见"""
        expect(page.locator(selector).first).to_be_visible()
