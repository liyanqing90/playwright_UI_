import sys
import time
from datetime import datetime
from typing import Optional, List

import pytest
import typer
from rich.console import Console
from rich.table import Table

from utils.config import Config, Browser, Environment, ProjectManager
from utils.logger import logger

console = Console()
app = typer.Typer()


def build_pytest_args(config: Config) -> List[str]:
    """
    构建pytest运行参数

    Args:
        config: 测试配置对象

    Returns:
        pytest命令行参数列表
    """
    # 构建测试文件路径
    test_path = f"{config.test_dir}/cases"
    if config.test_file:
        test_path = f"{test_path}/{config.test_file}"

    pytest_args = [
        test_path,
        "-v",
        "--tb=line",
        "-p",
        "no:warnings",
        "-s",
        "--alluredir=reports/allure-results",
        "--clean-alluredir",
    ]
    if config.marker:
        pytest_args.extend(["-m", config.marker])
    if config.keyword:
        pytest_args.extend(["-k", config.keyword])

    return pytest_args


def display_run_configuration(config: Config) -> None:
    """
    显示测试运行配置信息

    Args:
        config: 测试配置对象
    """
    table = Table(title="测试运行配置")
    table.add_column("配置项", style="cyan")
    table.add_column("值", style="magenta")

    table.add_row("浏览器", config.browser.value)
    table.add_row("运行模式", "有头模式" if config.headed else "无头模式")
    table.add_row("运行环境", config.env.value)
    table.add_row("项目", config.project)

    if config.test_file:
        table.add_row("测试文件", config.test_file)
    if config.marker:
        table.add_row("用例标记", config.marker)
    if config.keyword:
        table.add_row("筛选关键字", config.keyword)
    if config.base_url:
        table.add_row("基础URL", config.base_url)

    console.print(table)


def show_test_summary(start_time: float) -> None:
    """
    显示测试运行摘要信息

    Args:
        start_time: 测试开始时间戳
    """
    duration = time.time() - start_time

    table = Table(title="测试运行摘要")
    table.add_column("项目", style="cyan")
    table.add_column("值", style="magenta")

    table.add_row("运行时间", f"{duration:.2f} 秒")
    table.add_row("完成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    table.add_row("报告位置", "reports/allure-results")

    # console.print(table)


@app.command()
def main(
    marker: Optional[str] = typer.Option(
        None, "-m", "--marker", help="只运行特定标记的测试用例"
    ),
    keyword: Optional[str] = typer.Option(
        None, "-k", "--keyword", help="只运行匹配关键字的测试用例"
    ),
    headed: bool = typer.Option(True, "--headed", help="是否以有头模式运行浏览器"),
    browser: Browser = typer.Option(Browser.CHROMIUM, "--browser", help="指定浏览器"),
    env: Environment = typer.Option(Environment.PROD, "--env", help="指定环境"),
    project: str = typer.Option("demo", "--project", help="指定项目"),
    base_url: Optional[str] = typer.Option("", "--base-url", help="指定基础 URL"),
    test_file: Optional[str] = typer.Option("", "--test-file", help="指定测试文件"),
    no_parallel: bool = typer.Option(False, "--no-parallel", help="禁用并行执行"),
):
    """
    测试运行入口函数
    """
    # 验证项目是否存在
    project_manager = ProjectManager()
    available_projects = project_manager.get_available_projects()
    if project not in available_projects:
        console.print(f"[red]错误: 项目 '{project}' 不存在[/red]")
        console.print(f"[yellow]可用项目: {', '.join(available_projects)}[/yellow]")
        sys.exit(1)

    # 创建配置对象
    config = Config(
        marker=marker,
        keyword=keyword,
        headed=headed,
        browser=browser,
        env=env,
        project=project,
        test_file=(
            test_file + ".yaml"
            if test_file and not test_file.endswith((".yaml", ".yml"))
            else test_file
        ),
    )

    # 如果提供了base_url参数，覆盖配置中的base_url
    if base_url:
        config.base_url = base_url

    # 配置运行环境
    config.configure_environment()

    # 显示配置信息
    display_run_configuration(config)

    # 记录开始时间
    start_time = time.time()

    try:

        pytest_args = build_pytest_args(config)
        logger.info(f"使用参数运行pytest: {' '.join(pytest_args)}")
        exit_code = pytest.main(pytest_args)

        # 显示运行摘要
        show_test_summary(start_time)

        # 返回退出码
        sys.exit(exit_code)

    except KeyboardInterrupt:
        logger.error("测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试运行出错: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    typer.run(main)
