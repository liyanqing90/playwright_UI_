import json
from typing import Generator

import pytest
from playwright.sync_api import Browser, sync_playwright, Page

from page_objects.base_page import BasePage
from utils.logger import logger

log = logger

DEVICE = {}


def set_device(device):
    global DEVICE
    DEVICE = device


@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    """
    创建浏览器实例，session 级别的 fixture
    """
    with sync_playwright() as playwright:
        device = playwright.devices["iPhone 15 Pro"]
        set_device(device)
        browser = playwright.chromium.launch(headless=False)

        yield browser

        # 清理资源
        browser.close()


@pytest.fixture(scope="session")
def context(browser: Browser):
    context = browser.new_context(**DEVICE)
    cookie = convert_cookies(read_cookies())
    context.add_cookies(cookie)
    yield context
    storage_state = context.storage_state(path='config/storage_state.json')
    context.close()


@pytest.fixture(scope="function")
def page(context) -> Page:
    page = context.new_page()
    yield page
    page.close()


def read_cookies():
    with open("./config/cookie.json") as f:
        cookies = json.load(f)
    return cookies


# 将 expirationDate 转换为 Playwright 所需的 expires 字段
def convert_cookies(cookies):
    for cookie in cookies:
        # 将 expirationDate 转换为 Playwright 所需的 expires 字段
        if 'expirationDate' in cookie:
            cookie['expires'] = int(cookie['expirationDate'])  # Playwright 需要的是 Unix 时间戳
            del cookie['expirationDate']  # 删除原有的 expirationDate 字段

        if 'expires' in cookie:
            del cookie['expires']

        if cookie.get('sameSite') == 'unspecified':
            cookie['sameSite'] = 'None'  # 或者 'Lax' 或 'Strict'，根据实际需求
        # 如果 cookie 是会话 cookie，则删除 expires 字段
        if cookie.get('session', False):
            if 'expires' in cookie:
                del cookie['expires']
    return cookies


@pytest.fixture(scope="function")
def ui_helper(page):
    """
    创建UIHelper的fixture,用于封装页面操作
    :param page:
    :return:
    """
    ui = BasePage(page)
    yield ui

# def pytest_generate_tests(metafunc):  # noqa
#     """测试用例参数化功能实现"""
