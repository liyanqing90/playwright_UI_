import re
from typing import Dict, Any, Set

import allure

from src.test_step_executor import StepExecutor
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
    def __init__(
        self, case_data: Dict[str, Any], elements: Dict[str, Any], vars: Dict[str, Any]
    ):
        self.case_data = case_data
        self.elements = elements
        self.executed_fixtures: Set[str] = set()
        self.vars = vars

    def _replace_placeholders_in_string(self, text: str) -> str:
        """
        使用正则表达式替换字符串中的 ${...} 占位符，并使用 self.vars 中的值
        """

        def replace_callback(match):
            """
            re.sub 的回调函数，用于处理匹配到的占位符
            """
            placeholder_name = match.group(1)
            if placeholder_name in self.vars:  # 直接访问实例变量 self.vars
                # 将字典中的值转换为字符串进行替换
                return str(self.vars[placeholder_name])
            else:
                # 警告并保留原始占位符
                print(f"警告：变量字典中找不到占位符 '{placeholder_name}' 对应的值。")
                return match.group(0)

        # 只对字符串类型进行替换
        if isinstance(text, str):
            return re.sub(r"\$\{(.*?)\}", replace_callback, text)
        else:
            # 如果不是字符串，直接返回原始值
            return text

    def execute_test_case(self, page, ui_helper) -> None:
        """执行测试用例
        Args:
            page: Playwright页面对象
            ui_helper: UI操作帮助类
        """
        try:
            # 执行测试步骤
            step_executor = StepExecutor(page, ui_helper, self.elements)
            steps = self.case_data.get("steps")
            for step in steps:
                for key, value in step.items():
                    if "${" in value:
                        step[key] = self._replace_placeholders_in_string(value)
                step_executor.execute_step(step)
        finally:
            pass
