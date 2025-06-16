import json
import time
import types
from datetime import datetime
from pathlib import Path
from typing import Generator, Any

import pytest
from _pytest.python import Module
from playwright.sync_api import Page, Browser, sync_playwright

from config.constants import DEFAULT_TIMEOUT
from src.automation.runner import TestCaseGenerator
from src.automation.step_executor import StepExecutor
from src.case_utils import run_test_data, load_test_cases, load_moules
from src.core.base_page import BasePage
from src.core.plugin_compatibility import plugin_manager
from src.performance_monitor import performance_monitor
from utils.config import Config
from utils.dingtalk_notifier import ReportNotifier
from utils.logger import logger

DINGTALK_TOKEN = "636325ecf2302baf112f74ac54d8ef991de9b307c00bd168d3f2baa7df7f9113"
DINGTALK_SECRET = "SECa7e01bee3a34e05d1b57297a95b8920d8c257088979c49fa0b50889fd60c570c"

config = Config()


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """测试会话开始时启动插件系统和性能监控"""
    # 初始化插件系统
    try:
        plugin_count = plugin_manager.load_all_plugins()
        logger.info(f"插件系统已启动，成功加载 {plugin_count} 个插件")
        
        # 输出插件加载状态
        loaded_plugins = plugin_manager.list_plugins()
        if loaded_plugins:
            logger.info(f"已加载的插件: {', '.join(loaded_plugins.keys())}")
        else:
            logger.warning("没有加载任何插件")
            
    except Exception as e:
        logger.error(f"插件系统启动失败: {e}")
    
    # 启动性能监控
    try:
        # 使用轻量级模式启动性能监控，减少对测试执行的影响
        performance_monitor.start_monitoring()
        logger.info("性能监控已启动（轻量级模式）")
    except Exception as e:
        logger.error(f"启动性能监控失败: {e}")


@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    """
    创建浏览器实例，session 级别的 fixture
    """
    with sync_playwright() as playwright:
        browser = getattr(playwright, config.browser).launch(headless=not config.headed)
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def context(browser):
    """创建浏览器上下文"""
    context_options = config.browser_config or {}
    browser_context = browser.new_context(**context_options)
    browser_context.set_default_timeout(DEFAULT_TIMEOUT)
    yield browser_context
    # 测试结束后关闭上下文
    browser_context.close()


@pytest.fixture(scope="session")
def page(context) -> Generator[Page, Any, None]:
    """
    创建页面，session级别的fixture
    与ui_helper保持相同作用域，避免ScopeMismatch错误
    """
    page = context.new_page()
    yield page
    page.close()


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


@pytest.fixture(scope="session")
def ui_helper(page):
    """
    创建UIHelper的fixture,用于封装页面操作
    使用session作用域以避免重复初始化服务容器，提升性能
    :param page:
    :return:
    """
    ui = BasePage(page, base_url=config.base_url)
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
    # 使用session的开始时间，如果不存在则使用当前时间减去一个默认值
    session_start_time = getattr(terminalreporter, '_sessionstarttime', None)
    if session_start_time is None:
        # 如果没有_sessionstarttime属性，尝试从config或session中获取
        session_start_time = getattr(terminalreporter.config, '_session_start_time', time.time() - 1)
    duration = round(time.time() - session_start_time, 2)
    # 获取失败用例详情
    failures = []
    if terminalreporter.stats:
        for item in terminalreporter.stats.get("failed", []):
            # logger.debug(f"Processing failed test: {item.nodeid}")
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
    if file_path.suffix in [".yaml", "xlsx"]:
        if test_cases := load_test_cases(file_path):
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
    elements = run_test_data().get("elements")
    login_modules = load_moules().get("login")
    step_executor = StepExecutor(page, ui_helper, elements)
    for step in login_modules:
        step_executor.execute_step(step)

    return None


@pytest.fixture()
def fixture_demo():
    logger.debug("fixture demo")
    return "fixture demo"


def pytest_generate_tests(metafunc):  # noqa
    """测试用例参数化功能实现"""
    # 获取测试函数对应的测试数据
    func_name = metafunc.function.__name__
    params_data = getattr(metafunc.module, f"{func_name}_data", None)

    # 如果没有数据，跳过参数化
    if not params_data:
        return

    # 确保测试数据是列表形式
    if not isinstance(params_data, list):
        params_data = [params_data]

    # 生成测试ID
    ids = [
        value.get("description", f"用例{i + 1}") for i, value in enumerate(params_data)
    ]

    # 参数化
    metafunc.parametrize(
        "value",
        params_data,
        ids=ids,
        scope="function",
    )


@pytest.fixture()
def get_test_name(request):
    """返回当前测试用例的完整名称，包括参数化ID"""
    test_name = request.node.name
    # 将Unicode转义序列解码为实际的中文字符
    try:
        # 首先尝试标准的unicode_escape解码
        decoded_name = test_name.encode("utf-8").decode("unicode_escape")

        # 如果解码后看起来像乱码（包含特殊字符），尝试其他方法
        if any(ord(c) > 127 and ord(c) < 256 for c in decoded_name):
            # 这可能是UTF-8字节被错误解释，尝试重新编码
            try:
                decoded_name = decoded_name.encode("latin-1").decode("utf-8")
            except (UnicodeDecodeError, UnicodeEncodeError):
                # 如果还是失败，保持原来的解码结果
                pass

    except (UnicodeDecodeError, UnicodeEncodeError):
        # 如果解码失败，使用原始名称
        decoded_name = test_name

    # 移除DEBUG日志，减少重复信息
    return decoded_name

@pytest.fixture()
def current_test_name(request):
    """返回当前测试用例的基础名称（不包含参数化部分）"""
    test_name = request.node.name
    # 提取基础测试名称（去掉参数化部分）
    base_name = test_name.split("[")[0] if "[" in test_name else test_name
    logger.debug(f"当前测试用例基础名称: {base_name}")
    return base_name


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """
    测试会话结束时执行的钩子函数
    用于清理测试数据文件（在所有测试完成后只执行一次）
    """
    # 输出总体断言统计
    _output_final_assertion_stats()

    # 输出性能统计和关闭性能监控
    _output_final_performance_stats()

    try:
        variables_file = Path("test_data/variables.json")
        if variables_file.exists():
            variables_file.unlink()
            logger.info(f"已在测试会话结束时删除临时测试数据文件: {variables_file}")
    except Exception as e:
        logger.error(f"删除测试数据文件时出错: {e}")


def _output_final_assertion_stats():
    """输出最终的断言统计信息"""
    try:
        from src.assertion_manager import assertion_manager

        stats = assertion_manager.get_stats()

        if stats.total_assertions > 0:
            logger.info("=" * 60)
            logger.info("🎯 测试会话断言统计总结")
            logger.info("=" * 60)
            logger.info(f"📊 总断言数: {stats.total_assertions}")
            logger.info(f"✅ 通过断言: {stats.passed_assertions}")
            logger.info(f"❌ 失败断言: {stats.failed_assertions}")
            logger.info(f"   🔸 软断言失败: {stats.failed_soft_assertions}")
            logger.info(f"   🔸 硬断言失败: {stats.failed_hard_assertions}")
            logger.info(f"📈 断言成功率: {stats.success_rate:.2f}%")

            # 保存断言报告
            try:
                assertion_manager.save_report()
                logger.info("📄 断言报告已保存到: reports/assertion_report.json")
            except Exception as e:
                logger.error(f"保存断言报告失败: {e}")

            # 如果有失败的断言，输出汇总
            if stats.failed_assertions > 0:
                logger.warning("⚠️  失败断言汇总:")
                failed_by_type = {}
                for assertion in assertion_manager.get_failed_assertions():
                    test_case = assertion.test_case
                    if test_case not in failed_by_type:
                        failed_by_type[test_case] = {"soft": 0, "hard": 0}
                    failed_by_type[test_case][assertion.assertion_type] += 1

                for test_case, counts in failed_by_type.items():
                    logger.warning(f"   📋 {test_case}: 软断言失败 {counts['soft']} 个, 硬断言失败 {counts['hard']} 个")

            logger.info("=" * 60)
        else:
            logger.info("ℹ️  本次测试会话没有执行任何断言操作")

    except Exception as e:
        logger.error(f"输出断言统计时出错: {e}")


def _output_final_performance_stats():
    """输出最终的性能统计信息"""
    try:
        # 停止性能监控
        performance_monitor.stop_monitoring()

        # 获取性能统计
        report = performance_monitor.generate_report()

        logger.info("=" * 60)
        logger.info("🚀 测试会话性能统计总结")
        logger.info("=" * 60)

        summary = report["summary"]
        logger.info(f"📊 监控时长: {summary['monitoring_duration_minutes']:.1f} 分钟")
        logger.info(f"💾 内存使用: 峰值 {summary['peak_memory_mb']}MB, 平均 {summary['average_memory_mb']}MB")
        logger.info(f"🔥 CPU使用: 峰值 {summary['peak_cpu_percent']}%, 平均 {summary['average_cpu_percent']}%")
        logger.info(f"⏱️  总测试时间: {summary['total_test_time_seconds']} 秒")
        logger.info(f"🌐 浏览器实例: {summary['current_browser_instances']} 个")

        # 添加更详细的统计信息
        logger.info(f"📋 性能数据点: {report['metrics_count']} 个")

        # 获取变量管理器详细统计
        try:
            from utils.variable_manager import VariableManager
            vm = VariableManager()
            vm_stats = vm.get_stats()
            logger.info(f"🔧 变量管理: 获取 {vm_stats.get('get_count', 0)} 次, 设置 {vm_stats.get('set_count', 0)} 次, 缓存 {vm_stats.get('cache_size', 0)} 项")
        except Exception as e:
            logger.debug(f"获取变量管理器统计失败: {e}")

        # 输出优化建议
        if report["recommendations"]:
            logger.info("💡 性能优化建议:")
            for i, recommendation in enumerate(report["recommendations"], 1):
                logger.info(f"   {i}. {recommendation}")

        # 保存性能报告
        try:
            performance_monitor.save_report()
            logger.info("📄 性能报告已保存到: reports/performance_report.json")
        except Exception as e:
            logger.error(f"保存性能报告失败: {e}")

        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"输出性能统计时出错: {e}")





def pytest_collection_modifyitems(items) -> None:
    # item表示每个测试用例，解决用例名称中文显示问题
    def decode_unicode_text(text):
        """统一的Unicode解码函数"""
        try:
            # 首先尝试标准的unicode_escape解码
            decoded = text.encode("utf-8").decode("unicode_escape")

            # 如果解码后看起来像乱码，尝试其他方法
            if any(ord(c) > 127 and ord(c) < 256 for c in decoded):
                try:
                    decoded = decoded.encode("latin-1").decode("utf-8")
                except (UnicodeDecodeError, UnicodeEncodeError):
                    pass
            return decoded
        except (UnicodeDecodeError, UnicodeEncodeError):
            return text

    for item in items:
        try:
            item.name = decode_unicode_text(item.name)
            item._nodeid = decode_unicode_text(item._nodeid)
        except Exception as e:
            logger.warning(f"无法解码测试用例名称 {item.name}: {e}")
