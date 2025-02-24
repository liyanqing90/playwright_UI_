import functools
import os
from typing import Callable, Literal, Optional

import allure
from playwright.sync_api import Page

from constants import DEFAULT_TIMEOUT, DEFAULT_TYPE_DELAY
from utils.logger import logger
from utils.variable_manager import VariableManager


def handle_page_error(func: Callable) -> Callable:
    """统一的页面操作错误处理装饰器"""

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            logger.error(f"{func.__name__} 操作失败: {str(e)}")
            # 截图并添加到报告
            screenshot = self.page.screenshot()
            allure.attach(screenshot, name="错误截图", attachment_type=allure.attachment_type.PNG)
            raise

    return wrapper


def base_url():
    return os.environ.get('BASE_URL')


class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.variable_manager = VariableManager()
        self._setup_page_handlers()

    def _setup_page_handlers(self):
        """设置页面事件处理器"""
        self.page.on("pageerror", lambda exc: logger.error(f"页面错误: {exc}"))
        self.page.on("crash", lambda: logger.error("页面崩溃"))
        self.page.on("console", lambda msg: logger.debug(f"控制台 {msg.type}: {msg.text}"))

    def _wait_for_element(self, selector: str, state: Literal["attached", "detached", "hidden", "visible"] = "visible",
                          timeout: int = DEFAULT_TIMEOUT):
        """统一的元素等待方法"""
        try:
            self.page.wait_for_selector(selector, state=state, timeout=timeout)
        except Exception as e:
            logger.error(f"等待元素 {selector} 超时 (state={state})")
            raise

    @handle_page_error
    @allure.step("导航到 {url}")
    def navigate(self, url: str):
        """导航到指定URL"""
        self.page.goto(url)
        self.page.wait_for_load_state("domcontentloaded")

    @handle_page_error
    @allure.step("暂停")
    def pause(self):
        self.page.pause()

    @handle_page_error
    @allure.step("点击元素 {selector}")
    def click(self, selector: str):
        """点击元素"""
        self._wait_for_element(selector)
        self.page.locator(selector).first.click()

    @handle_page_error
    @allure.step("点击元素 {selector}")
    def upload_file(self, selector: str, file_path: str):
        """上传文件"""
        # self._wait_for_element(selector)
        self.page.locator(selector).set_input_files(file_path)

    @handle_page_error
    @allure.step("输入文本 {text}")
    def fill(self, selector: str, text: str):
        """在输入框中填写文本"""
        resolved_text = self._resolve_variables(text)
        self._wait_for_element(selector)
        self.page.fill(selector, resolved_text)

    @handle_page_error
    @allure.step("按键 {key}")
    def press_key(self, selector: str, key: str):
        """在元素上按键"""
        self._wait_for_element(selector)
        self.page.locator(selector).press(key)

    @handle_page_error
    @allure.step("获取元素文本")
    def get_text(self, selector: str) -> str:
        """获取元素文本"""
        self._wait_for_element(selector)
        return self.page.inner_text(selector)

    @handle_page_error
    @allure.step("断言元素文本")
    def assert_text(self, selector: str, expected_text: str):
        """断言元素文本"""
        actual_text = self.get_text(selector)
        resolved_expected = self._resolve_variables(expected_text)
        assert actual_text == resolved_expected, \
            f"断言失败: 期望文本为 '{resolved_expected}', 实际文本为 '{actual_text}'"

    @handle_page_error
    @allure.step("断言元素可见性")
    def assert_visible(self, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT):
        """断言元素可见"""
        self._wait_for_element(selector, timeout=timeout)

    @handle_page_error
    @allure.step("断言元素不可见")
    def assert_not_visible(self, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT):
        """断言元素不可见"""
        is_visible = self.page.is_visible(selector, timeout=timeout)
        assert not is_visible, f"断言失败: 元素 {selector} 仍然可见"

    @handle_page_error
    @allure.step("存储变量 {name}")
    def store_variable(self, name: str, value: str, scope: str = "global"):
        """存储变量"""
        self.variable_manager.set_variable(name, value, scope)

    @handle_page_error
    @allure.step("存储元素文本")
    def store_text(self, selector: str, variable_name: str, scope: str = "global"):
        """存储元素文本到变量"""
        text = self.get_text(selector)
        logger.debug(f"存储变量 {variable_name}: {text}")
        self.store_variable(variable_name, text, scope)

    @handle_page_error
    @allure.step("存储元素属性")
    def store_attribute(self, selector: str, attribute: str, variable_name: str, scope: str = "global"):
        """存储元素属性到变量"""
        self._wait_for_element(selector)
        value = self.page.get_attribute(selector, attribute)
        self.store_variable(variable_name, value, scope)

    @handle_page_error
    @allure.step("刷新页面")
    def refresh(self):
        """刷新页面"""
        self.page.reload()
        self.page.wait_for_load_state("networkidle")

    @handle_page_error
    @allure.step("等待指定时间")
    def wait_for_timeout(self, timeout: int):
        """等待指定时间"""
        self.page.wait_for_timeout(timeout)

    @handle_page_error
    @allure.step("等待加载状态")
    def wait_for_load_state(self, state: Literal["domcontentloaded", "load", "networkidle"] | None = None):
        """等待页面加载状态"""
        self.page.wait_for_load_state(state)

    def _resolve_variables(self, text: str) -> str:
        """解析文本中的变量引用"""
        if not text or "${" not in text:
            return text

        result = text
        while "${" in result:
            start = result.find("${")
            end = result.find("}", start)
            if end == -1:
                break

            var_name = result[start + 2:end]
            var_value = self.variable_manager.get_variable(var_name, "global", "")
            result = result[:start] + str(var_value) + result[end + 1:]

        return result

    def wait_and_click(self, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT):
        """等待元素可点击并点击"""
        element = self.page.wait_for_selector(
            selector,
            state="visible",
            timeout=timeout
        )
        element.click()

    def wait_and_fill(self, selector: str, text: str, timeout: Optional[int] = DEFAULT_TIMEOUT):
        """等待元素可见并输入文本"""
        element = self.page.wait_for_selector(
            selector,
            state="visible",
            timeout=timeout
        )
        element.fill(text)

    def close(self):
        self.page.close()

    @staticmethod
    def reuse_browser_context(context):
        """复用浏览器上下文"""
        return context.new_page()

    @handle_page_error
    @allure.step("悬停在元素 {selector}")
    def hover(self, selector: str):
        """鼠标悬停在元素上"""
        self.page.hover(selector)

    @handle_page_error
    @allure.step("双击元素 {selector}")
    def double_click(self, selector: str):
        """双击元素"""
        self._wait_for_element(selector)
        self.page.dblclick(selector)

    @handle_page_error
    @allure.step("右键点击元素 {selector}")
    def right_click(self, selector: str):
        """右键点击元素"""
        self._wait_for_element(selector)
        self.page.click(selector, button='right')

    @handle_page_error
    @allure.step("选择下拉框选项")
    def select_option(self, selector: str, value: str):
        """选择下拉框选项"""
        self._wait_for_element(selector)
        self.page.locator(selector).select_option(value=value)

    @handle_page_error
    @allure.step("拖拽元素")
    def drag_and_drop(self, source: str, target: str):
        """拖拽元素"""
        self._wait_for_element(source)
        self._wait_for_element(target)
        source_element = self.page.locator(source)
        target_element = self.page.locator(target)
        source_element.drag_to(target_element)

    @handle_page_error
    @allure.step("获取元素值")
    def get_value(self, selector: str) -> str:
        """获取元素的value属性值"""
        self._wait_for_element(selector)
        return self.page.input_value(selector)

    @handle_page_error
    @allure.step("滚动到元素")
    def scroll_into_view(self, selector: str):
        """将元素滚动到可视区域"""
        self._wait_for_element(selector)
        self.page.locator(selector).scroll_into_view_if_needed()

    @handle_page_error
    @allure.step("滚动到指定位置")
    def scroll_to(self, x: int = 0, y: int = 0):
        """滚动到指定坐标"""
        self.page.evaluate(f"window.scrollTo({x}, {y})")

    @handle_page_error
    @allure.step("聚焦元素")
    def focus(self, selector: str):
        """聚焦到指定元素"""
        self._wait_for_element(selector)
        self.page.focus(selector)

    @handle_page_error
    @allure.step("使元素失焦")
    def blur(self, selector: str):
        """使元素失去焦点"""
        self._wait_for_element(selector)
        self.page.evaluate("element => element.blur()", self.page.locator(selector))

    @handle_page_error
    @allure.step("模拟键盘输入")
    def type(self, selector: str, text: str, delay: int = DEFAULT_TYPE_DELAY):
        """模拟人工输入文字，带输入延迟"""
        self._wait_for_element(selector)
        self.page.locator(selector).type(text, delay=delay)

    @handle_page_error
    @allure.step("清空输入框")
    def clear(self, selector: str):
        """清空输入框内容"""
        self._wait_for_element(selector)
        self.page.locator(selector).clear()

    @handle_page_error
    @allure.step("进入iframe")
    def enter_frame(self, selector: str):
        """进入iframe"""
        self._wait_for_element(selector)
        return self.page.frame_locator(selector)

    @handle_page_error
    @allure.step("接受弹窗")
    def accept_alert(self, selector, value=None):
        dialog_message = None  # 用于存储弹框内容
        if not value:
            value = {}

        def handle_dialog(dialog):
            nonlocal dialog_message  # 声明为外部变量
            if message := value.get("message"):
                dialog.accept(message)
            else:
                dialog.accept()
            dialog_message = dialog.message

        self.page.once("dialog", handle_dialog)
        self.page.click(selector)
        return dialog_message

    @handle_page_error
    @allure.step("拒绝弹窗")
    def dismiss_alert(self, selector, value=None):
        dialog_message = None  # 用于存储弹框内容

        if not value:
            value = {}

        def handle_dialog(dialog):
            nonlocal dialog_message  # 声明为外部变量

            if message := value.get("message"):
                dialog.dismiss(message)
            else:
                dialog.dismiss()
            dialog_message = dialog.message

        self.page.once("dialog", handle_dialog)
        self.page.click(selector)
        return dialog_message

    @handle_page_error
    @allure.step("切换窗口")
    def switch_window(self, url_contains: str = None, title_contains: str = None):
        """切换到指定窗口"""
        pages = self.page.context.pages
        for page in pages:
            if url_contains and url_contains in page.url:
                self.page = page
                return
            if title_contains and title_contains in page.title():
                self.page = page
                return
        raise ValueError("未找到匹配的窗口")

    @handle_page_error
    @allure.step("关闭当前窗口")
    def close_window(self):
        """关闭当前窗口"""
        if len(self.page.context.pages) == 1:
            raise RuntimeError("无法关闭最后一个窗口")
        self.page.close()
        self.page = self.page.context.pages[-1]

    @handle_page_error
    @allure.step("等待新窗口打开")
    def wait_for_new_window(self) -> Page:
        """等待新窗口打开并返回新窗口"""
        with self.page.context.expect_page() as new_page_info:
            new_page = new_page_info.value
            new_page.wait_for_load_state()
            return new_page

    @handle_page_error
    @allure.step("等待元素消失")
    def wait_for_element_hidden(self, selector: str, timeout: Optional[int] = DEFAULT_TIMEOUT):
        """等待元素消失"""
        return self.page.wait_for_selector(selector, timeout=timeout, state="hidden")

    def get_element_count(self, selector: str) -> int:
        """获取元素数量"""
        return self.page.locator(selector).count()

    @handle_page_error
    @allure.step("执行JavaScript: {script}")
    def execute_script(self, script: str):
        """执行JavaScript代码"""
        return self.page.evaluate(script)

    @handle_page_error
    @allure.step("保存当前页面截图")
    def capture_screenshot(self, path: str):
        """主动保存页面截图"""
        self.page.screenshot(path=path)

    @handle_page_error
    @allure.step("操作Cookie")
    def manage_cookies(self, action: str, **kwargs):
        """管理Cookie"""
        if action == "add":
            required = {"name", "value", "url"}
            if not required.issubset(kwargs):
                raise ValueError("添加Cookie缺少必要参数: name, value, url")
            self.page.context.add_cookies([kwargs])
        elif action == "get":
            return self.page.context.cookies()
        elif action == "delete":
            self.page.context.clear_cookies()

    def get_element_attribute(self, selector: str, attribute: str) -> str:
        """获取元素属性"""
        self._wait_for_element(selector)
        return self.page.get_attribute(selector, attribute)

    def get_current_url(self) -> str:
        """获取当前页面URL"""
        return self.page.url

    def get_page_title(self) -> str:
        """获取页面标题"""
        return self.page.title()
