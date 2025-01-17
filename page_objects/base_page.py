import functools
import os
from typing import Callable, Literal

import allure
from playwright.sync_api import Page

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
                          timeout: int = 10000):
        """统一的元素等待方法"""
        try:
            self.page.wait_for_selector(selector, state=state, timeout=timeout)
        except Exception as e:
            logger.error(f"等待元素 {selector} 超时 (state={state})")
            raise

    @handle_page_error
    @allure.step("导航到 {url}")
    def goto(self, url: str):
        """导航到指定URL"""
        base_rul = base_url()
        if "http" not in url:
            url = base_rul + url
        self.page.goto(url)
        # self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    @handle_page_error
    @allure.step("暂停")
    def pause(self):
        self.page.pause()

    @handle_page_error
    @allure.step("点击元素 {selector}")
    def click(self, selector: str):
        """点击元素"""
        self._wait_for_element(selector)
        self.page.click(selector)

    @handle_page_error
    @allure.step("点击元素 {selector}")
    def upload_file(self, selector: str, file_path: str):
        """上传文件"""
        self._wait_for_element(selector)
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
    @allure.step("等待元素可见")
    def wait_for_visible(self, selector: str, timeout: int = 5000):
        """等待元素可见"""
        self._wait_for_element(selector, timeout=timeout)

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
    def assert_visible(self, selector: str, timeout: int = 5000):
        """断言元素可见"""
        is_visible = self.page.is_visible(selector, timeout=timeout)
        assert is_visible, f"断言失败: 元素 {selector} 未可见"

    @handle_page_error
    @allure.step("断言元素不可见")
    def assert_not_visible(self, selector: str, timeout: int = 5000):
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
    @allure.step("等待超时")
    def wait_timeout(self, timeout: int):
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

    def wait_and_click(self, selector: str, timeout: int = None):
        """等待元素可点击并点击"""
        element = self.page.wait_for_selector(
            selector,
            state="visible",
            timeout=timeout or self.config.timeout
        )
        element.click()

    def wait_and_fill(self, selector: str, text: str, timeout: int = None):
        """等待元素可见并输入文本"""
        element = self.page.wait_for_selector(
            selector,
            state="visible",
            timeout=timeout or self.config.timeout
        )
        element.fill(text)

    def close(self):
        self.page.close()

    @staticmethod
    def reuse_browser_context(context):
        """复用浏览器上下文"""
        return context.new_page()
