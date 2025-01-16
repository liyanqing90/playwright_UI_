from typing import Dict, Any, Set

import allure
from _pytest.fixtures import FixtureRequest

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
    def __init__(self, test_data: Dict[str, Any], elements: Dict[str, Any], request: FixtureRequest):
        self.test_data = test_data
        self.elements = elements
        self.executed_cases: Set[str] = set()
        self.executed_fixtures: Set[str] = set()
        self.request: FixtureRequest = request  # 保存 pytest 的 request 对象

    def execute_test_case(self, case: Dict[str, Any], page, ui_helper) -> None:
        case_name = case["name"]
        # 检查循环依赖
        self._check_circular_dependencies(case)

        # 执行依赖的测试用例
        self._execute_dependencies(case, page, ui_helper)

        # 执行必需的 fixtures
        self._execute_fixtures(case)

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

        self.executed_cases.add(case_name)

    def _check_circular_dependencies(self, case: Dict[str, Any]) -> None:
        visited = set()

        def check_dependency(current_case):
            if current_case["name"] in visited:
                raise ValueError(f"Circular dependency detected for case: {current_case['name']}")

            visited.add(current_case["name"])
            depends = current_case.get("depends_on", [])

            for dep in depends:
                dep_case = next((c for c in self.test_data if c["name"] == dep), {})
                if dep_case:
                    check_dependency(dep_case)

            visited.remove(current_case["name"])

        check_dependency(case)

    def _execute_dependencies(self, case: Dict[str, Any], page, ui_helper) -> None:
        depends = case.get("depends_on", [])

        for dep in depends:
            if dep not in self.executed_cases:
                dep_case = next((c for c in self.test_data if c["name"] == dep), {})
                if not dep_case:
                    raise ValueError(f"Dependent case not found: {dep}")

                with allure.step(f"执行依赖用例: {dep}"):
                    self.execute_test_case(dep_case, page, ui_helper)

    def _execute_fixtures(self, case: Dict[str, Any]) -> None:
        """执行测试用例所需的 fixtures"""
        required_fixtures = case.get("fixtures", [])

        if not required_fixtures:
            return

        with allure.step("执行 Fixtures"):
            log.info(f"Executing fixtures for case: {case['name']}")
            for fixture_name in required_fixtures:
                if fixture_name not in self.executed_fixtures:
                    log.info(f"执行 fixture: {fixture_name}")
                    try:
                        # 通过 request.getfixturevalue 获取和执行 fixture
                        fixture_value = self.request.getfixturevalue(fixture_name)
                        self.executed_fixtures.add(fixture_name)
                        if fixture_value:
                            log.info(f"Fixture {fixture_name} return {fixture_value}")
                    except Exception as e:
                        log.error(f"Fixture '{fixture_name}' 执行失败: {str(e)}")
                        raise
