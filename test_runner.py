import sys
import time
from datetime import datetime
from typing import Optional

import pytest
import typer
from rich.console import Console
from rich.table import Table

from utils.config import Config, Browser, Environment, Project
from utils.logger import logger

console = Console()
app = typer.Typer()


def build_pytest_args(config):
    marker = config.marker
    keyword = config.keyword
    test_dir = config.test_dir

    pytest_args = [
        f"{test_dir}/cases",
        '-v',
        "-p", "no:warnings",
        "--report-log=report.json",
        "-s",
        "--alluredir=reports/allure-results",
        "--clean-alluredir"
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


@app.command()
def main(
        marker: Optional[str] = typer.Option(None, "-m", "--marker", help="只运行特定标记的测试用例"),
        keyword: Optional[str] = typer.Option(None, "-k", "--keyword", help="只运行匹配关键字的测试用例"),
        headed: bool = typer.Option(False, "--headed", help="是否以有头模式运行浏览器"),
        browser: Browser = typer.Option(Browser.CHROMIUM, "--browser", help="指定浏览器"),
        env: Environment = typer.Option(Environment.PROD, "--env", help="指定环境"),
        project: Project = typer.Option(Project.DEMO, "--project", help="指定项目"),
        base_url: Optional[str] = typer.Option("", "--base-url", help="指定基础 URL"),
):
    config = Config(
        marker=marker,
        keyword=keyword,
        headed=headed,
        browser=browser,
        env=env,
        project=project,
        base_url=base_url
    )
    # 配置运行环境
    config.configure_environment()
    # 构建pytest运行参数

    # 显示和记录运行配置
    display_run_configuration(config, marker)

    # 记录开始时间
    start_time = time.time()

    try:
        # 运行测试
        exit_code = pytest.main(build_pytest_args(config))

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


if __name__ == '__main__':
    typer.run(main)
