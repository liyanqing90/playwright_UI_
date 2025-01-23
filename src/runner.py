import types
from inspect import Parameter, Signature

import allure
import pytest
from playwright.async_api import Page

from src.case_utils import run_test_data
from src.test_case_executor import CaseExecutor

_DEFAULT_FIXTURES = ["page", "ui_helper"]


def build_test_signature(fixtures: list) -> Signature:
    conflict = set(fixtures) & set(_DEFAULT_FIXTURES)
    if conflict:
        raise ValueError(f"禁止覆盖默认 fixtures: {conflict}")
    parameters = [Parameter(name, Parameter.POSITIONAL_OR_KEYWORD)
                  for name in _DEFAULT_FIXTURES + fixtures]
    return Signature(parameters)


class TestCaseGenerator(pytest.Item):

    def __init__(self, module: types.ModuleType, name, **kw):
        super().__init__(name, **kw)
        self.datas = run_test_data()
        self.test_cases = self.datas.get("test_cases", [])
        self.test_data = self.datas.get("test_data", {})
        self.elements = self.datas.get("elements", {})
        self.module: types.ModuleType = module  # 动态创建的 module 模型
        self.module_variable = {}  # 模块变量

    def generate(self):
        """主生成方法"""
        for case in self.test_cases:
            test_func = self._create_test_function(case)
            setattr(self.module, test_func.__name__, test_func)

    def _create_test_function(self, case: dict):
        """动态生成测试函数（优化版）"""
        case_name = case["name"]
        depends = case.get("depends_on", [])
        fixtures = case.get("fixtures", [])

        # 使用闭包绑定当前 case 数据
        def _test_closure(page, ui_helper, **kwargs):
            self.execute_test(
                case=case,
                elements=self.elements,
                page=page,
                ui_helper=ui_helper,
                **kwargs
            )

        # 添加依赖标记
        marked_func = pytest.mark.dependency(name=case_name, depends=depends)(_test_closure)

        # 设置函数元数据
        marked_func.__name__ = case_name
        marked_func.__doc__ = case.get("description", "")
        marked_func.__signature__ = build_test_signature(fixtures)
        return marked_func

    def execute_test(self, case: dict, page: Page, ui_helper, **kwargs) -> None:
        with allure.step(f"执行用例: {case['name']}"):
            executor = CaseExecutor(self.test_data, self.elements)
            executor.execute_test_case(case, page, ui_helper)

    def runtest(self):
        """
        运行测试用例
        """
        pass
