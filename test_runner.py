import sys
import time
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from utils.config import Config
from utils.logger import logger

log = logger

import pytest
from src.test_case_executor import CaseExecutor
from src.load_data import TestDataConverter

console = Console()
app = typer.Typer()


def build_pytest_args(marker: Optional[str], keyword: Optional[str]):
    """构建pytest运行参数"""
    pytest_args = [
        'test_scripts/test_ui.py',
        '-v',
        "-p no:warnings",
    ]
    if marker:
        pytest_args.extend(["-m", marker])
    if keyword:
        pytest_args.extend(["-k", keyword])
    return pytest_args


def display_run_configuration(settings: Config, marker: Optional[str]):
    """显示运行配置信息"""
    table = Table(title="测试运行配置")
    table.add_column("配置项", style="cyan")
    table.add_column("值", style="magenta")

    table.add_row("浏览器", settings.browser.value)
    table.add_row("运行模式", "有头模式" if settings.headed else "无头模式")
    table.add_row("运行环境", settings.env.value)
    if marker:
        table.add_row("用例标记", marker)

    console.print(table)


def show_test_summary(start_time: float):
    """显示测试摘要信息"""
    table = Table(title="测试运行摘要")
    table.add_column("项目", style="cyan")
    table.add_column("值", style="magenta")

    duration = time.time() - start_time
    table.add_row("运行时间", f"{duration:.2f} 秒")
    table.add_row("完成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    table.add_row("报告位置", "reports/allure-results")

    # console.print(table)


def main(
        marker: Optional[str] = typer.Option(None, "-m", "--marker", help="只运行特定标记的测试用例 (例如: smoke)"),
        keyword: Optional[str] = typer.Option(None, "-k", "--keyword", help="只运行匹配关键字的测试用例"),
        config: Config = typer.Option(Config()),
):
    # 配置运行环境
    config.configure_environment()
    # 构建pytest运行参数
    pytest_args = build_pytest_args(marker, keyword)

    # 显示和记录运行配置
    display_run_configuration(config, marker)

    # 记录开始时间
    start_time = time.time()

    try:
        # 运行测试
        exit_code = pytest.main(pytest_args)

        # 显示和记录测试摘要
        show_test_summary(start_time)

        # 退出程序
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.error("[bold red]测试被用户中断[/bold red]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试运行出错: {str(e)}")
        sys.exit(1)


data_merger = TestDataConverter()

data = data_merger.convert_excel_data()
test_cases = data['cases']['test_cases']
test_data = data['test_data']['test_data']
elements = data['elements']['elements']


# 直接在测试文件中定义测试函数
def create_test_function(case):
    def test_func(request, page, ui_helper):
        executor = CaseExecutor(test_data, elements, request)
        executor.execute_test_case(case, page, ui_helper)

    return test_func


# 为每个测试用例创建测试函数
for test_case in test_cases:
    test_name = f"test_{test_case['name']}"
    _function = create_test_function(test_case)
    _function.__doc__ = test_case.get('description', '')
    # 将测试函数添加到当前模块的命名空间
    globals()[test_name] = _function

if __name__ == '__main__':
    typer.run(main)
    # pytest.main([
    #     __file__,
    #     "-v",
    #     "--alluredir=reports/allure-results",
    #     "--clean-alluredir"
    # ])
