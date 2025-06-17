"""报告处理插件
提供多种格式的测试报告生成和处理功能
"""

import datetime
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List

import allure
from playwright.sync_api import Page

from src.automation.commands.base_command import Command, CommandFactory
from utils.logger import logger


@dataclass
class ReportConfig:
    """报告配置"""

    output_dir: str = "reports"
    format: str = "html"
    include_screenshots: bool = True
    include_page_source: bool = False
    include_network_logs: bool = False
    include_console_logs: bool = False
    timestamp_format: str = "%Y%m%d_%H%M%S"
    auto_open: bool = False


@dataclass
class TestResult:
    """测试结果数据结构"""

    test_name: str
    status: str  # passed, failed, skipped
    start_time: datetime.datetime
    end_time: datetime.datetime
    duration: float
    error_message: Optional[str] = None
    screenshots: List[str] = None
    page_source: Optional[str] = None
    network_logs: List[Dict] = None
    console_logs: List[Dict] = None
    steps: List[Dict] = None

    def __post_init__(self):
        if self.screenshots is None:
            self.screenshots = []
        if self.network_logs is None:
            self.network_logs = []
        if self.console_logs is None:
            self.console_logs = []
        if self.steps is None:
            self.steps = []


class ReportHandler(ABC):
    """报告处理器基类"""

    @abstractmethod
    def generate(self, results: List[TestResult], config: ReportConfig) -> str:
        """生成报告"""
        pass

    @abstractmethod
    def get_format(self) -> str:
        """获取报告格式"""
        pass


class HTMLReportHandler(ReportHandler):
    """HTML报告处理器"""

    def get_format(self) -> str:
        return "html"

    def generate(self, results: List[TestResult], config: ReportConfig) -> str:
        """生成HTML报告"""
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime(config.timestamp_format)
        report_file = output_dir / f"test_report_{timestamp}.html"

        # 生成HTML内容
        html_content = self._generate_html_content(results, config)

        # 写入文件
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"HTML报告已生成: {report_file}")
        return str(report_file)

    def _generate_html_content(
        self, results: List[TestResult], config: ReportConfig
    ) -> str:
        """生成HTML内容"""
        # 统计信息
        total = len(results)
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")

        # 计算总耗时
        total_duration = sum(r.duration for r in results)

        # HTML模板
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .summary {{ display: flex; justify-content: space-around; margin-bottom: 30px; }}
        .summary-item {{ text-align: center; padding: 15px; border-radius: 5px; }}
        .summary-item.total {{ background-color: #e3f2fd; }}
        .summary-item.passed {{ background-color: #e8f5e8; }}
        .summary-item.failed {{ background-color: #ffebee; }}
        .summary-item.skipped {{ background-color: #fff3e0; }}
        .summary-item h3 {{ margin: 0; font-size: 24px; }}
        .summary-item p {{ margin: 5px 0 0 0; color: #666; }}
        .test-results {{ margin-top: 20px; }}
        .test-item {{ border: 1px solid #ddd; margin-bottom: 10px; border-radius: 5px; }}
        .test-header {{ padding: 15px; background-color: #f8f9fa; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }}
        .test-header.passed {{ border-left: 4px solid #4caf50; }}
        .test-header.failed {{ border-left: 4px solid #f44336; }}
        .test-header.skipped {{ border-left: 4px solid #ff9800; }}
        .test-details {{ padding: 15px; display: none; background-color: #fafafa; }}
        .status {{ padding: 4px 8px; border-radius: 3px; color: white; font-size: 12px; }}
        .status.passed {{ background-color: #4caf50; }}
        .status.failed {{ background-color: #f44336; }}
        .status.skipped {{ background-color: #ff9800; }}
        .error-message {{ background-color: #ffebee; padding: 10px; border-radius: 3px; margin: 10px 0; color: #c62828; }}
        .screenshot {{ margin: 10px 0; }}
        .screenshot img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 3px; }}
        .steps {{ margin: 10px 0; }}
        .step {{ padding: 5px 0; border-bottom: 1px solid #eee; }}
        .step:last-child {{ border-bottom: none; }}
        pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; }}
    </style>
    <script>
        function toggleDetails(element) {{
            const details = element.nextElementSibling;
            details.style.display = details.style.display === 'none' ? 'block' : 'none';
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>测试报告</h1>
            <p>生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="summary-item total">
                <h3>{total}</h3>
                <p>总计</p>
            </div>
            <div class="summary-item passed">
                <h3>{passed}</h3>
                <p>通过</p>
            </div>
            <div class="summary-item failed">
                <h3>{failed}</h3>
                <p>失败</p>
            </div>
            <div class="summary-item skipped">
                <h3>{skipped}</h3>
                <p>跳过</p>
            </div>
        </div>
        
        <div class="test-results">
            <h2>测试结果详情</h2>
            {self._generate_test_items_html(results, config)}
        </div>
    </div>
</body>
</html>
        """

        return html_template

    def _generate_test_items_html(
        self, results: List[TestResult], config: ReportConfig
    ) -> str:
        """生成测试项HTML"""
        items_html = []

        for result in results:
            # 测试项头部
            duration_str = f"{result.duration:.2f}s"
            header_html = f"""
            <div class="test-item">
                <div class="test-header {result.status}" onclick="toggleDetails(this)">
                    <div>
                        <strong>{result.test_name}</strong>
                        <span class="status {result.status}">{result.status.upper()}</span>
                    </div>
                    <div>
                        <span>耗时: {duration_str}</span>
                    </div>
                </div>
                <div class="test-details">
            """

            # 测试详情
            details_html = []

            # 时间信息
            details_html.append(
                f"""
                <p><strong>开始时间:</strong> {result.start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>结束时间:</strong> {result.end_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>执行时长:</strong> {duration_str}</p>
            """
            )

            # 错误信息
            if result.error_message:
                details_html.append(
                    f"""
                    <div class="error-message">
                        <strong>错误信息:</strong><br>
                        <pre>{result.error_message}</pre>
                    </div>
                """
                )

            # 截图
            if config.include_screenshots and result.screenshots:
                details_html.append("<h4>截图:</h4>")
                for screenshot in result.screenshots:
                    if os.path.exists(screenshot):
                        details_html.append(
                            f"""
                            <div class="screenshot">
                                <img src="{screenshot}" alt="截图" />
                            </div>
                        """
                        )

            # 页面源码
            if config.include_page_source and result.page_source:
                details_html.append(
                    f"""
                    <h4>页面源码:</h4>
                    <pre>{result.page_source[:1000]}{'...' if len(result.page_source) > 1000 else ''}</pre>
                """
                )

            # 执行步骤
            if result.steps:
                details_html.append("<h4>执行步骤:</h4>")
                details_html.append('<div class="steps">')
                for i, step in enumerate(result.steps, 1):
                    step_status = step.get("status", "unknown")
                    step_action = step.get("action", "unknown")
                    step_desc = step.get("description", "")
                    details_html.append(
                        f"""
                        <div class="step">
                            <strong>步骤 {i}:</strong> {step_action} - {step_desc}
                            <span class="status {step_status}">{step_status}</span>
                        </div>
                    """
                    )
                details_html.append("</div>")

            # 网络日志
            if config.include_network_logs and result.network_logs:
                details_html.append(
                    f"""
                    <h4>网络日志:</h4>
                    <pre>{json.dumps(result.network_logs[:5], indent=2, ensure_ascii=False)}</pre>
                """
                )

            # 控制台日志
            if config.include_console_logs and result.console_logs:
                details_html.append(
                    f"""
                    <h4>控制台日志:</h4>
                    <pre>{json.dumps(result.console_logs[:10], indent=2, ensure_ascii=False)}</pre>
                """
                )

            # 组合完整的测试项HTML
            item_html = header_html + "".join(details_html) + "</div></div>"
            items_html.append(item_html)

        return "".join(items_html)


class JSONReportHandler(ReportHandler):
    """JSON报告处理器"""

    def get_format(self) -> str:
        return "json"

    def generate(self, results: List[TestResult], config: ReportConfig) -> str:
        """生成JSON报告"""
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime(config.timestamp_format)
        report_file = output_dir / f"test_report_{timestamp}.json"

        # 转换为字典格式
        report_data = {
            "summary": {
                "total": len(results),
                "passed": sum(1 for r in results if r.status == "passed"),
                "failed": sum(1 for r in results if r.status == "failed"),
                "skipped": sum(1 for r in results if r.status == "skipped"),
                "total_duration": sum(r.duration for r in results),
                "generated_at": datetime.datetime.now().isoformat(),
            },
            "results": [self._convert_result_to_dict(result) for result in results],
        }

        # 写入文件
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"JSON报告已生成: {report_file}")
        return str(report_file)

    def _convert_result_to_dict(self, result: TestResult) -> Dict:
        """将测试结果转换为字典"""
        result_dict = asdict(result)
        # 转换时间格式
        result_dict["start_time"] = result.start_time.isoformat()
        result_dict["end_time"] = result.end_time.isoformat()
        return result_dict


class AllureReportHandler(ReportHandler):
    """Allure报告处理器"""

    def get_format(self) -> str:
        return "allure"

    def generate(self, results: List[TestResult], config: ReportConfig) -> str:
        """生成Allure报告"""
        # Allure报告通常在测试执行过程中生成
        # 这里主要是添加额外的附件和信息

        for result in results:
            # 添加测试结果信息
            with allure.step(f"测试: {result.test_name}"):
                allure.attach(
                    json.dumps(
                        asdict(result), indent=2, ensure_ascii=False, default=str
                    ),
                    name="测试结果详情",
                    attachment_type=allure.attachment_type.JSON,
                )

                # 添加截图
                if config.include_screenshots and result.screenshots:
                    for i, screenshot in enumerate(result.screenshots):
                        if os.path.exists(screenshot):
                            with open(screenshot, "rb") as f:
                                allure.attach(
                                    f.read(),
                                    name=f"截图_{i+1}",
                                    attachment_type=allure.attachment_type.PNG,
                                )

                # 添加页面源码
                if config.include_page_source and result.page_source:
                    allure.attach(
                        result.page_source,
                        name="页面源码",
                        attachment_type=allure.attachment_type.HTML,
                    )

        logger.info("Allure报告信息已添加")
        return "allure_results"


class ReportHandlerPlugin:
    """报告处理插件主类"""

    def __init__(self):
        self.name = "report_handler"
        self.version = "1.0.0"
        self.description = "报告处理插件，提供多种格式的测试报告生成和处理功能"
        self.author = "Playwright UI Framework"

        # 插件配置
        self.config = ReportConfig()

        # 报告处理器注册表
        self.handlers: Dict[str, ReportHandler] = {}

        # 测试结果存储
        self.test_results: List[TestResult] = []

        # 注册内置处理器
        self._register_builtin_handlers()

        # 注册命令
        self._register_commands()

    def _register_commands(self):
        """注册插件命令"""
        # 注册报告生成命令
        CommandFactory.register(["generate_report", "生成报告"])(GenerateReportCommand)
        CommandFactory.register(["attach_screenshot", "添加截图"])(
            AttachScreenshotCommand
        )
        CommandFactory.register(["attach_page_source", "添加页面源码"])(
            AttachPageSourceCommand
        )
        CommandFactory.register(["add_test_result", "添加测试结果"])(
            AddTestResultCommand
        )
        CommandFactory.register(["clear_results", "清空结果"])(ClearResultsCommand)

    def _register_builtin_handlers(self):
        """注册内置报告处理器"""
        self.register_handler(HTMLReportHandler())
        self.register_handler(JSONReportHandler())
        self.register_handler(AllureReportHandler())

    def register_handler(self, handler: ReportHandler):
        """注册报告处理器"""
        self.handlers[handler.get_format()] = handler
        logger.debug(f"已注册报告处理器: {handler.get_format()}")

    def unregister_handler(self, format_name: str):
        """注销报告处理器"""
        if format_name in self.handlers:
            del self.handlers[format_name]
            logger.debug(f"已注销报告处理器: {format_name}")

    def generate_report(
        self, format_name: str, config: Optional[ReportConfig] = None
    ) -> str:
        """生成报告"""
        if format_name not in self.handlers:
            raise ValueError(f"不支持的报告格式: {format_name}")

        config = config or self.config
        handler = self.handlers[format_name]

        return handler.generate(self.test_results, config)

    def add_test_result(self, result: TestResult):
        """添加测试结果"""
        self.test_results.append(result)
        logger.debug(f"已添加测试结果: {result.test_name}")

    def clear_results(self):
        """清空测试结果"""
        self.test_results.clear()
        logger.debug("已清空测试结果")

    def attach_screenshot(self, page: Page, name: Optional[str] = None) -> str:
        """添加截图"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        name = name or f"screenshot_{timestamp}"

        # 确保截图目录存在
        screenshot_dir = Path(self.config.output_dir) / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        # 生成截图文件路径
        screenshot_path = screenshot_dir / f"{name}.png"

        # 截图
        screenshot = page.screenshot(path=str(screenshot_path))

        # 添加到Allure报告
        allure.attach(screenshot, name=name, attachment_type=allure.attachment_type.PNG)

        logger.debug(f"已添加截图: {screenshot_path}")
        return str(screenshot_path)

    def attach_page_source(self, page: Page, name: Optional[str] = None):
        """添加页面源码"""
        name = name or "page_source"
        page_source = page.content()

        # 添加到Allure报告
        allure.attach(
            page_source, name=name, attachment_type=allure.attachment_type.HTML
        )

        logger.debug(f"已添加页面源码: {name}")

    def get_available_formats(self) -> List[str]:
        """获取可用的报告格式"""
        return list(self.handlers.keys())

    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.debug(f"更新配置: {key} = {value}")


# 插件命令实现
class GenerateReportCommand(Command):
    """生成报告命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> Any:
        """执行生成报告命令"""
        try:
            # 获取插件实例
            plugin = getattr(ui_helper, "_report_handler_plugin", None)
            if not plugin:
                plugin = ReportHandlerPlugin()
                setattr(ui_helper, "_report_handler_plugin", plugin)

            # 解析参数
            if isinstance(value, dict):
                format_name = value.get("format", "html")
                config_data = value.get("config", {})

                # 创建配置
                config = ReportConfig(**config_data)
            else:
                format_name = str(value)
                config = None

            # 生成报告
            report_path = plugin.generate_report(format_name, config)

            # 如果指定了变量名，保存到变量管理器
            var_name = step.get("variable")
            if var_name and hasattr(ui_helper, "variable_manager"):
                ui_helper.variable_manager.set_variable(var_name, report_path)

            return report_path

        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            raise


class AttachScreenshotCommand(Command):
    """添加截图命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> Any:
        """执行添加截图命令"""
        try:
            # 获取插件实例
            plugin = getattr(ui_helper, "_report_handler_plugin", None)
            if not plugin:
                plugin = ReportHandlerPlugin()
                setattr(ui_helper, "_report_handler_plugin", plugin)

            # 获取页面对象
            page = getattr(ui_helper, "page", None)
            if not page:
                raise ValueError("页面对象不可用")

            # 解析参数
            if isinstance(value, dict):
                name = value.get("name")
            else:
                name = str(value) if value else None

            # 添加截图
            screenshot_path = plugin.attach_screenshot(page, name)

            # 如果指定了变量名，保存到变量管理器
            var_name = step.get("variable")
            if var_name and hasattr(ui_helper, "variable_manager"):
                ui_helper.variable_manager.set_variable(var_name, screenshot_path)

            return screenshot_path

        except Exception as e:
            logger.error(f"添加截图失败: {e}")
            raise


class AttachPageSourceCommand(Command):
    """添加页面源码命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> Any:
        """执行添加页面源码命令"""
        try:
            # 获取插件实例
            plugin = getattr(ui_helper, "_report_handler_plugin", None)
            if not plugin:
                plugin = ReportHandlerPlugin()
                setattr(ui_helper, "_report_handler_plugin", plugin)

            # 获取页面对象
            page = getattr(ui_helper, "page", None)
            if not page:
                raise ValueError("页面对象不可用")

            # 解析参数
            if isinstance(value, dict):
                name = value.get("name")
            else:
                name = str(value) if value else None

            # 添加页面源码
            plugin.attach_page_source(page, name)

            return "页面源码已添加"

        except Exception as e:
            logger.error(f"添加页面源码失败: {e}")
            raise


class AddTestResultCommand(Command):
    """添加测试结果命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> Any:
        """执行添加测试结果命令"""
        try:
            # 获取插件实例
            plugin = getattr(ui_helper, "_report_handler_plugin", None)
            if not plugin:
                plugin = ReportHandlerPlugin()
                setattr(ui_helper, "_report_handler_plugin", plugin)

            # 解析参数
            if not isinstance(value, dict):
                raise ValueError("添加测试结果需要字典格式的参数")

            # 创建测试结果对象
            result_data = value.copy()

            # 处理时间字段
            if "start_time" in result_data and isinstance(
                result_data["start_time"], str
            ):
                result_data["start_time"] = datetime.datetime.fromisoformat(
                    result_data["start_time"]
                )
            if "end_time" in result_data and isinstance(result_data["end_time"], str):
                result_data["end_time"] = datetime.datetime.fromisoformat(
                    result_data["end_time"]
                )

            result = TestResult(**result_data)

            # 添加测试结果
            plugin.add_test_result(result)

            return f"测试结果已添加: {result.test_name}"

        except Exception as e:
            logger.error(f"添加测试结果失败: {e}")
            raise


class ClearResultsCommand(Command):
    """清空结果命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> Any:
        """执行清空结果命令"""
        try:
            # 获取插件实例
            plugin = getattr(ui_helper, "_report_handler_plugin", None)
            if not plugin:
                plugin = ReportHandlerPlugin()
                setattr(ui_helper, "_report_handler_plugin", plugin)

            # 清空结果
            plugin.clear_results()

            return "测试结果已清空"

        except Exception as e:
            logger.error(f"清空结果失败: {e}")
            raise


# 插件初始化和清理函数
def plugin_init():
    """插件初始化函数"""
    logger.info("报告处理插件已初始化")


def plugin_cleanup():
    """插件清理函数"""
    logger.info("报告处理插件已清理")


# 创建插件实例
report_handler_plugin = ReportHandlerPlugin()
