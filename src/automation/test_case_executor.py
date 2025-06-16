from typing import Dict, Any, Set

import allure

from src.assertion_manager import assertion_manager
# 导入重构后的StepExecutor
from src.automation.step_executor import StepExecutor
from src.core.mixins.error_reporter import generate_final_error_report
from utils.logger import logger

log = logger

def _cleanup_test_environment(case: Dict[str, Any]) -> None:
    with allure.step("测试环境清理"):
        log.debug(f"Cleaning up test environment for case: {case['name']}")
        # fixture 的清理会由 pytest 自动处理

def _setup_test_environment(case: Dict[str, Any]) -> None:
    with allure.step("测试环境准备"):
        log.debug(f"Setting up test environment for case: {case['name']}")
        # 添加环境准备代码

class CaseExecutor:
    def __init__(self, case_data: Dict[str, Any], elements: Dict[str, Any]):
        self.case_data = case_data
        self.elements = elements
        self.executed_fixtures: Set[str] = set()

    def execute_test_case(self, page, ui_helper, test_name=None) -> None:
        """执行测试用例
        Args:
            page: Playwright页面对象
            ui_helper: UI操作帮助类
            test_name: 测试用例名称
        """
        import time
        from src.performance_monitor import performance_monitor

        # 记录测试开始时间
        test_start_time = time.time()

        case_name = test_name if test_name else "未知测试用例"

        # 设置当前测试用例名称到断言管理器
        assertion_manager.set_current_test_case(case_name)
        log.info(f"🚀 执行测试用例: {case_name}")

        try:
            # 执行测试步骤
            step_executor = StepExecutor(page, ui_helper, self.elements)

            if isinstance(self.case_data, list):
                if self.case_data and isinstance(self.case_data[0], dict):
                    steps = self.case_data[0].get("steps", [])
                else:
                    steps = []
            elif isinstance(self.case_data, dict):
                steps = self.case_data.get("steps", [])
            else:
                steps = []

            # 执行所有步骤
            for step in steps:
                step_executor.execute_step(step)

            # 测试执行完成，在finally中统一输出结果
            pass

        except Exception as e:
            # 只在最终层记录错误，避免重复记录
            if not hasattr(e, "_logged") or not getattr(e, "_logged", False):
                from src.core.mixins.error_deduplication import error_dedup_manager
                
                error_info = getattr(e, "_error_info", str(e))
                if error_dedup_manager.should_log_error(
                    error_message=error_info,
                    error_type=type(e).__name__
                ):
                    log.error(f"❌ 测试用例 {case_name} 执行失败: {error_info}")
                
                setattr(e, "_logged", True)
            raise
        finally:
            # 记录测试执行时间
            test_end_time = time.time()
            test_duration = test_end_time - test_start_time
            performance_monitor.record_test_execution_time(test_duration)

            # 输出简化的测试结果统计
            self._output_test_summary(case_name, test_duration)
            
            # 生成错误去重报告（仅在测试会话结束时）
            if hasattr(self, '_is_last_test') and self._is_last_test:
                try:
                    log.info("📊 生成错误去重效果报告...")
                    report_files = generate_final_error_report()
                    if report_files.get('summary_report'):
                        log.info(f"📋 错误摘要报告: {report_files['summary_report']}")
                    if report_files.get('detailed_report'):
                        log.info(f"📄 详细错误报告: {report_files['detailed_report']}")
                except Exception as e:
                    log.warning(f"生成错误报告时出现问题: {e}")

    def _output_test_summary(self, case_name: str, test_duration: float):
        """输出简化的测试结果摘要"""
        stats = assertion_manager.get_stats()

        # 构建状态图标
        if stats.failed_assertions > 0:
            status_icon = "❌"
            status_text = "失败"
        else:
            status_icon = "✅"
            status_text = "通过"

        # 构建断言信息
        if stats.total_assertions > 0:
            assertion_info = f"断言 {stats.passed_assertions}/{stats.total_assertions}"
            if stats.failed_assertions > 0:
                assertion_info += f" (失败: {stats.failed_assertions})"
        else:
            assertion_info = "无断言"

        # 输出简化的一行摘要
        log.info(f"{status_icon} {case_name} | {status_text} | {assertion_info} | 耗时 {test_duration:.2f}s")

        if stats.failed_assertions > 0:
            failed_assertions = assertion_manager.get_failed_assertions()
            log.warning(f"   失败断言详情:")
            for i, assertion in enumerate(failed_assertions, 1):
                log.warning(f"   {i}. [{assertion.assertion_type}断言] {assertion.step_description}")
                log.warning(f"      错误: {assertion.error_message}")
                if assertion.expected is not None:
                    log.warning(f"      期望: {assertion.expected}")
                if assertion.actual is not None:
                    log.warning(f"      实际: {assertion.actual}")

    def _output_assertion_stats(self, case_name: str):
        """保留原方法以兼容性，但不再使用"""
        pass
