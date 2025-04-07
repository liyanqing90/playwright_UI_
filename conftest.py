import json
import os
import time
import types
from datetime import datetime
from pathlib import Path
from typing import Generator, Any, List

import pytest
from _pytest.python import Module
from playwright.sync_api import Page, Browser, sync_playwright

from page_objects.base_page import BasePage
from src.case_utils import run_test_data
from src.runner import TestCaseGenerator
from src.test_step_executor import StepExecutor
from utils.config import Config
from utils.dingtalk_notifier import ReportNotifier
from utils.logger import logger
from utils.yaml_handler import YamlHandler

DINGTALK_TOKEN = "636325ecf2302baf112f74ac54d8ef991de9b307c00bd168d3f2baa7df7f9113"
DINGTALK_SECRET = "SECa7e01bee3a34e05d1b57297a95b8920d8c257088979c49fa0b50889fd60c570c"

config = Config()


@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    """
    创建浏览器实例，session 级别的 fixture
    """
    with sync_playwright() as playwright:
        browser = getattr(playwright, config.browser).launch(headless=not config.headed)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser):
    """创建浏览器上下文"""
    context_options = config.browser_config or {}
    browser_context = browser.new_context(**context_options)
    yield browser_context
    # 测试结束后关闭上下文
    browser_context.close()


@pytest.fixture(scope="function")
def page(context) -> Generator[Page, Any, None]:
    """
    创建页面，function级别的fixture
    """
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="function")
def screenshot_fixture(request, page):
    """
    截图管理fixture，使用Playwright原生的截图功能
    仅在测试失败时捕获截图
    """
    # 执行测试用例
    yield

    # 如果测试失败，捕获截图
    if request.node.rep_call.failed if hasattr(request.node, "rep_call") else False:
        test_name = request.node.name
        logger.info(f"测试用例 {test_name} 失败，捕获截图")

        # 创建截图目录
        screenshot_dir = "reports/screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)

        # 生成截图文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(
            screenshot_dir, f"failure_{test_name}_{timestamp}.png"
        )

        try:
            # 使用Playwright的截图功能
            page.screenshot(
                path=screenshot_path,
                full_page=True,  # 捕获完整页面
                timeout=5000,  # 5秒超时
            )
            logger.info(f"失败截图已保存: {screenshot_path}")
        except Exception as e:
            logger.error(f"保存失败截图时出错: {e}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    pytest hook，用于获取测试结果状态
    供screenshot_fixture使用
    """
    # 执行hook的其余部分
    outcome = yield
    rep = outcome.get_result()

    # 设置测试节点的rep_call属性
    setattr(item, f"rep_{rep.when}", rep)


def read_cookies():
    with open("./config/cookie.json") as f:
        cookies = json.load(f)
    return cookies


# 将 expirationDate 转换为 Playwright 所需的 expires 字段
def convert_cookies(cookies):
    for cookie in cookies:
        # 将 expirationDate 转换为 Playwright 所需的 expires 字段
        if "expirationDate" in cookie:
            cookie["expires"] = int(
                cookie["expirationDate"]
            )  # Playwright 需要的是 Unix 时间戳
            del cookie["expirationDate"]  # 删除原有的 expirationDate 字段

        if "expires" in cookie:
            del cookie["expires"]

        if cookie.get("sameSite") == "unspecified":
            cookie["sameSite"] = "None"  # 或者 'Lax' 或 'Strict'，根据实际需求
        # 如果 cookie 是会话 cookie，则删除 expires 字段
        if cookie.get("session", False):
            if "expires" in cookie:
                del cookie["expires"]
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
    env = os.getenv("ENV", config.env.value)
    duration = round(time.time() - terminalreporter._sessionstarttime, 2)
    # 获取失败用例详情
    failures = []
    if terminalreporter.stats:
        for item in terminalreporter.stats.get("failed", []):
            logger.debug(f"Processing failed test: {item.nodeid}")
            error_msg = extract_assertion_message(item.sections)
            failures.append(
                {
                    "test_case": item.nodeid.split("::")[-1],
                    "reason": error_msg,
                }
            )

    report_data = {
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "environment": env,
        "total_tests": terminalreporter._numcollected,
        "passed": terminalreporter._numcollected
        - len(terminalreporter.stats.get("failed", [])),
        "failed": len(terminalreporter.stats.get("failed", [])),
        "skipped": len(terminalreporter.stats.get("skipped", [])),
        "duration": duration,
        "failures": failures,
    }

    # report_notifier().notify(report_data)


def extract_assertion_message(log_list):
    for log_type, message in log_list:
        if "Step execution failed:" in message:
            # 清除ANSI转义码及其相关内容
            clean_msg = ""
            i = 0
            while i < len(message):
                if message[i] == "\x1b":
                    # 跳过转义序列
                    while i < len(message) and message[i] != "m":
                        i += 1
                    i += 1  # 跳过 'm'
                else:
                    clean_msg += message[i]
                    i += 1

            # 提取断言信息
            start = clean_msg.find("Step execution failed:") + len(
                "Step execution failed:"
            )

            # 返回清理后的信息
            result = clean_msg[start:].strip()
            # 移除可能残留的 [0m 或类似序列
            if "[0m" in result:
                result = result.replace("[0m", "")
            return result.strip()

    return None


def pytest_collect_file(file_path: Path, parent):  # noqa
    datas = run_test_data()
    yaml_handler = YamlHandler()
    if file_path.suffix in [".yaml", "xlsx"]:
        if test_data := yaml_handler.load_yaml(file_path):
            test_cases = test_data["test_cases"]
            py_module, module = create_py_module(file_path, parent, test_cases, datas)
            py_module._getobj = lambda: module  # 返回 pytest 模块对象
            return py_module
    return None


def create_py_module(file_path: Path, parent, test_cases, datas):
    """创建并生成 py 模块"""
    py_module = Module.from_parent(parent, path=file_path)
    module = types.ModuleType(file_path.stem)  # 动态创建 module
    # 解析 YAML 并生成测试函数
    generator = TestCaseGenerator.from_parent(
        parent, module=module, name=module.__name__, test_cases=test_cases, datas=datas
    )
    generator.generate()
    return py_module, module


@pytest.fixture()
def login(page, ui_helper, request):
    yaml = YamlHandler()
    test_dir = os.environ.get("TEST_DIR")
    elements = yaml.load_yaml_dir(f"{test_dir}/elements/").get("elements")
    login_steps = yaml.load_yaml_dir(f"{test_dir}/steps/").get("steps").get("login")
    step_executor = StepExecutor(page, ui_helper, elements)
    for step in login_steps:
        step_executor.execute_step(step)

    return None


@pytest.fixture()
def fixture_demo():
    logger.debug("fixture demo")
    return "fixture demo"
