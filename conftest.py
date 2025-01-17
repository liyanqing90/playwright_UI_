import json
import os
import time
import types
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest
from _pytest.python import Module
from playwright.sync_api import Browser, sync_playwright, Page

from page_objects.base_page import BasePage
from src.runner import RunYaml
from src.test_step_executor import StepExecutor
from utils.config import Config
from utils.dingtalk_notifier import ReportNotifier
from utils.logger import logger
from utils.yaml_handler import YamlHandler

log = logger

DINGTALK_TOKEN = "636325ecf2302baf112f74ac54d8ef991de9b307c00bd168d3f2baa7df7f9113"
DINGTALK_SECRET = "SECa7e01bee3a34e05d1b57297a95b8920d8c257088979c49fa0b50889fd60c570c"

DEVICE = {}

# BROWSER_CONFIG = dict(os.environ['BROWSER_CONFIG'])
config = Config()


@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    """
    创建浏览器实例，session 级别的 fixture
    """
    with sync_playwright() as playwright:
        browser = getattr(playwright, config.browser).launch(headless=False)
        # browser = playwright.chromium.launch(headless=False)

        yield browser

        # 清理资源
        browser.close()


@pytest.fixture(scope="session")
def context(browser: Browser):
    context_options = {}
    browser_config = config.browser_config
    if "user_agent" in browser_config:
        context_options["user_agent"] = browser_config.get("user_agent")
    if "viewport" in browser_config:
        context_options["viewport"] = browser_config["viewport"]
    if "device_scale_factor" in browser_config:
        context_options["device_scale_factor"] = browser_config.get("device_scale_factor")
    if "is_mobile" in browser_config:
        context_options["is_mobile"] = browser_config.get("is_mobile")
    if "has_touch" in browser_config:
        context_options["has_touch"] = browser_config.get("has_touch")

    context = browser.new_context(**context_options)
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


def report_notifier():
    return ReportNotifier(DINGTALK_TOKEN, DINGTALK_SECRET)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """测试结束时发送通知"""
    from utils.config import Config
    import os

    # 获取环境配置
    config = Config()
    env = os.getenv('ENV', config.env.value)
    duration = round(time.time() - terminalreporter._sessionstarttime, 2)
    # 获取失败用例详情
    failures = []
    if terminalreporter.stats:
        for item in terminalreporter.stats.get('failed', []):
            log.info(f"Processing failed test: {item.nodeid}")
            error_msg = extract_assertion_message(item.sections)
            failures.append({
                "test_case": item.nodeid.split("::")[-1],
                "reason": error_msg,
            })

    report_data = {
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "environment": env,
        "total_tests": terminalreporter._numcollected,
        "passed": terminalreporter._numcollected - len(terminalreporter.stats.get('failed', [])),
        "failed": len(terminalreporter.stats.get('failed', [])),
        "skipped": len(terminalreporter.stats.get('skipped', [])),
        "duration": duration,
        "failures": failures
    }

    # report_notifier().notify(report_data)


def extract_assertion_message(log_list):
    for log_type, message in log_list:
        if "Step execution failed:" in message:
            # 清除ANSI转义码及其相关内容
            clean_msg = ''
            i = 0
            while i < len(message):
                if message[i] == '\x1b':
                    # 跳过转义序列
                    while i < len(message) and message[i] != 'm':
                        i += 1
                    i += 1  # 跳过 'm'
                else:
                    clean_msg += message[i]
                    i += 1

            # 提取断言信息
            start = clean_msg.find("Step execution failed:") + len("Step execution failed:")

            # 返回清理后的信息
            result = clean_msg[start:].strip()
            # 移除可能残留的 [0m 或类似序列
            if '[0m' in result:
                result = result.replace('[0m', '')
            return result.strip()

    return None


def pytest_collect_file(file_path: Path, parent):  # noqa
    if file_path.suffix in [".yaml", "xlsx"]:
        py_module = Module.from_parent(parent, path=file_path)
        # 动态创建 module
        module = types.ModuleType(file_path.stem)
        # 解析 yaml 内容
        name = module.__name__
        run = RunYaml.from_parent(parent, module=module, name=name)
        run.collect_case()
        # 重写属性
        py_module._getobj = lambda: module  # noqa
        return py_module




@pytest.fixture()
def login(page, ui_helper, request):
    yaml = YamlHandler()
    test_dir = os.environ.get('TEST_DIR')
    elements = yaml.load_yaml_dir(f"{test_dir}/elements/").get("elements")
    login_steps = yaml.load_yaml_dir(f"{test_dir}/steps/").get("steps").get("login")
    step_executor = StepExecutor(page, ui_helper, elements)
    for step in login_steps:
        step_executor.execute_step(step)

    return None
