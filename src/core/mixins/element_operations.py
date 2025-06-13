"""
元素操作混入类
包含基础的元素操作方法
"""
from typing import Any, Optional, List, Literal
from playwright.sync_api import Page
from config.constants import DEFAULT_TIMEOUT, DEFAULT_TYPE_DELAY
from utils.logger import logger
from .decorators import handle_page_error


class ElementOperationsMixin:
    """元素操作混入类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    # _locator方法已移至BasePage中，提供统一的高性能元素定位

    @handle_page_error(description="点击元素")
    def click(self, selector: str):
        """点击元素"""
        self._locator(selector).first.click(timeout=DEFAULT_TIMEOUT, force=True)

    @handle_page_error(description="输入文本")
    def fill(self, selector: str, value: Any):
        """在输入框中填写文本"""
        resolved_text = self.variable_manager.replace_variables_refactored(value)
        # 确保传递给 Playwright 的 fill 方法的值是字符串类型
        if resolved_text is not None:
            resolved_text = str(resolved_text)
        self._locator(selector).first.fill(resolved_text)

    @handle_page_error(description="按键")
    def press_key(self, selector: str, key: str):
        """在元素上按键"""
        self._locator(selector).first.press(key)

    @handle_page_error(description="获取元素文本")
    def get_text(self, selector: str) -> str:
        """获取元素文本"""
        return self._locator(selector).first.inner_text()

    @handle_page_error(description="鼠标悬停在元素")
    def hover(self, selector: str):
        """鼠标悬停在元素上"""
        self._locator(selector).first.hover()

    @handle_page_error(description="双击元素")
    def double_click(self, selector: str):
        """双击元素"""
        self._locator(selector).first.dblclick()

    @handle_page_error(description="右键点击元素")
    def right_click(self, selector: str):
        """右键点击元素"""
        self._locator(selector).first.click(button="right")

    @handle_page_error(description="选择下拉框选项")
    def select_option(self, selector: str, value: str):
        """选择下拉框选项"""
        self._locator(selector).first.select_option(value=value)

    @handle_page_error(description="拖拽元素")
    def drag_and_drop(self, source: str, target: str):
        """拖拽元素"""
        source_element = self._locator(source).first
        target_element = self._locator(target).first
        source_element.drag_to(target_element)

    @handle_page_error(description="获取元素值")
    def get_value(self, selector: str) -> str:
        """获取元素的value属性值"""
        return self._locator(selector).first.input_value()

    @handle_page_error(description="滚动到元素")
    def scroll_into_view(self, selector: str):
        """将元素滚动到可视区域"""
        self._locator(selector).first.scroll_into_view_if_needed()

    @handle_page_error(description="聚焦元素")
    def focus(self, selector: str):
        """聚焦到指定元素"""
        self._locator(selector).first.focus()

    @handle_page_error(description="使元素失焦")
    def blur(self, selector: str):
        """使元素失去焦点"""
        self.page.evaluate("element => element.blur()", self._locator(selector).first)

    @handle_page_error(description="键入文本")
    def type(self, selector: str, text: str, delay: int = DEFAULT_TYPE_DELAY):
        """模拟人工输入文字，带输入延迟"""
        self._locator(selector).first.type(text, delay=delay)

    @handle_page_error(description="清空输入框")
    def clear(self, selector: str):
        """清空输入框内容"""
        self._locator(selector).first.clear()

    @handle_page_error(description="上传文件")
    def upload_file(self, selector: str, file_path: str):
        """上传文件"""
        self.page.set_input_files(selector, file_path)

    def wait_and_click(self, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT):
        """等待元素可点击并点击"""
        self._locator(selector, timeout=timeout).first.click()

    def wait_and_fill(
        self, selector: str, text: Any, timeout: Optional[int] = DEFAULT_TIMEOUT
    ):
        """等待元素可见并输入文本"""
        # 确保传递给 Playwright 的 fill 方法的值是字符串类型
        if text is not None:
            text = str(text)
        self._locator(selector, timeout=timeout).first.fill(text)

    def get_element_count(self, selector: str) -> int:
        """获取元素数量"""
        locator = self._locator(selector, state="attached")
        logger.debug(f"获取元素数量: {selector}{locator}")
        return locator.count()

    @handle_page_error(description="获取所有匹配元素")
    def get_all_elements(self, selector: str) -> List[Any]:
        """获取所有匹配的元素"""
        elements = self._locator(selector, state="attached").all()
        return elements

    @handle_page_error(description="获取元素属性")
    def get_element_attribute(self, selector: str, attribute: str) -> str:
        """获取元素属性"""
        self._locator(selector, state="attached")
        return self._locator(selector).first.get_attribute(attribute)
