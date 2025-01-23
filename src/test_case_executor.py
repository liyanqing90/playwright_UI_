from typing import Dict, Any, Set

import allure

from src.test_step_executor import StepExecutor
from utils.logger import logger

log = logger


def _cleanup_test_environment(case: Dict[str, Any]) -> None:
    with allure.step("测试环境清理"):
        log.info(f"Cleaning up test environment for case: {case['name']}")
        # fixture 的清理会由 pytest 自动处理


def _setup_test_environment(case: Dict[str, Any]) -> None:
    with allure.step("测试环境准备"):
        log.info(f"Setting up test environment for case: {case['name']}")
        # 添加环境准备代码


class CaseExecutor:

    def __init__(self, test_data: Dict[str, Any], elements: Dict[str, Any]):
        self.test_data = test_data
        self.elements = elements
        self.executed_fixtures: Set[str] = set()

    def execute_test_case(self, case: Dict[str, Any], page, ui_helper) -> None:
        case_name = case["name"]

        # # 执行测试用例前的准备工作
        # self._setup_test_environment(case)
        try:
            # 执行测试步骤
            step_executor = StepExecutor(page, ui_helper, self.elements)
            steps = self.test_data[case_name]["steps"]

            for step in steps:
                step_executor.execute_step(step)

        finally:
            pass
        #     # 清理测试环境
        #     self._cleanup_test_environment(case)
