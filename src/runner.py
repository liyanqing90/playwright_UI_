import types
from inspect import Parameter, Signature

import allure
import pytest
from playwright.sync_api import Page

from src.case_utils import run_test_data
from src.test_case_executor import CaseExecutor


class RunYaml(pytest.Item):
    """运行yaml"""

    def __init__(self, module: types.ModuleType, name, **kw):
        super().__init__(name, **kw)
        self.data = run_test_data()
        self.test_cases = self.data.get('test_cases')
        self.test_data = self.data['test_data']
        self.elements = self.data['elements']
        self.module: types.ModuleType = module  # 动态创建的 module 模型
        self.module_variable = {}  # 模块变量
        self.context = {}

    def collect_case(self):
        for case in self.test_cases:
            function_name = case.get("name")
            config_fixtures = case.get('fixtures', [])
            depends = case.get("depends_on", [])
            self.context.update(__builtins__)  # noqa 内置函数加载
            fixture = self.function_fixture(config_fixtures)

            f = self.create_test_function(
                case,
                name=function_name,
                func=self.runtest,
                fixture=fixture,
                depends=depends,
            )
            setattr(self.module, function_name, f)

    def runtest(self, args, page, ui_helper, request):  # 修改：runtest接收page和ui_helper
        with allure.step(f"执行用例: {args.get('case')['name']}"):
            executor = CaseExecutor(self.test_data, self.elements, request)
            executor.execute_test_case(args.get("case"), page, ui_helper)

    def function_fixture(self, fixtures) -> list:
        """测试函数传 fixture"""
        # 测试函数的默认请求参数
        return [
            Parameter(fixture, Parameter.POSITIONAL_OR_KEYWORD)
            for fixture in ["page", "ui_helper", "request"] + fixtures  # 添加 request fixture
        ]

    def create_test_function(self, case, name, func, fixture, depends):
        @pytest.mark.dependency(name=name, depends=depends)
        def test_function(page: Page, ui_helper, request, case=case, **kwargs):  # 添加 request fixture
            kwargs.update({"case": case})
            func(kwargs, page, ui_helper, request)

        test_function.__signature__ = Signature(fixture)
        test_function.__name__ = name
        return test_function
