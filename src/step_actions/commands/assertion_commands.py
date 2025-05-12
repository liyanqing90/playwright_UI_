"""
断言相关的命令
"""

import json
from typing import Dict, Any

from src.step_actions.action_types import StepAction
from src.step_actions.commands.base_command import Command, CommandFactory
from src.step_actions.expression_evaluator import evaluate_math_expression


@CommandFactory.register(StepAction.ASSERT_TEXT)
class AssertTextCommand(Command):
    """断言文本命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        expected = step.get("expected", value)
        ui_helper.assert_text(selector=selector, expected=expected)


@CommandFactory.register(StepAction.HARD_ASSERT_TEXT)
class HardAssertTextCommand(Command):
    """硬断言文本命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        expected = step.get("expected", value)
        ui_helper.hard_assert_text(selector=selector, expected=expected)


@CommandFactory.register(StepAction.ASSERT_TEXT_CONTAINS)
class AssertTextContainsCommand(Command):
    """断言文本包含命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        expected = step.get("expected", value)
        ui_helper.assert_text_contains(selector=selector, expected=expected)


@CommandFactory.register(StepAction.ASSERT_URL)
class AssertUrlCommand(Command):
    """断言URL命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        expected = step.get("expected", value)
        ui_helper.assert_url(expected=expected)


@CommandFactory.register(StepAction.ASSERT_URL_CONTAINS)
class AssertUrlContainsCommand(Command):
    """断言URL包含命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        expected = step.get("expected", value)
        ui_helper.assert_url_contains(expected=expected)


@CommandFactory.register(StepAction.ASSERT_TITLE)
class AssertTitleCommand(Command):
    """断言标题命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        expected = step.get("expected", value)
        ui_helper.assert_title(expected=expected)


@CommandFactory.register(StepAction.ASSERT_ELEMENT_COUNT)
class AssertElementCountCommand(Command):
    """断言元素数量命令，支持数学表达式"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        expected = step.get("expected", value)
        expression = step.get("expression")

        # 如果提供了表达式，则计算表达式的值
        if expression:
            try:
                expected = evaluate_math_expression(
                    expression, ui_helper.variable_manager
                )
                from utils.logger import logger

                logger.info(f"计算表达式: {expression} = {expected}")
            except Exception as e:
                from utils.logger import logger

                logger.error(f"计算表达式错误: {expression} - {e}")
                raise

        ui_helper.assert_element_count(selector=selector, expected=expected)


@CommandFactory.register(StepAction.ASSERT_VISIBLE)
class AssertVisibleCommand(Command):
    """断言可见命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.assert_visible(selector=selector)


@CommandFactory.register(StepAction.ASSERT_EXISTS)
class AssertExistsCommand(Command):
    """断言存在命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.assert_exists(selector=selector)


@CommandFactory.register(StepAction.ASSERT_NOT_EXISTS)
class AssertNotExistsCommand(Command):
    """断言不存在命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.assert_not_exists(selector=selector)


@CommandFactory.register(StepAction.ASSERT_ENABLED)
class AssertEnabledCommand(Command):
    """断言启用命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.assert_element_enabled(selector=selector)


@CommandFactory.register(StepAction.ASSERT_DISABLED)
class AssertDisabledCommand(Command):
    """断言禁用命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.assert_element_disabled(selector=selector)


@CommandFactory.register(StepAction.ASSERT_ATTRIBUTE)
class AssertAttributeCommand(Command):
    """断言属性命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        attribute = step.get("attribute")
        expected = step.get("expected", value)
        ui_helper.assert_attribute(
            selector=selector, attribute=attribute, expected=expected
        )


@CommandFactory.register(StepAction.ASSERT_VALUE)
class AssertValueCommand(Command):
    """断言值命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        expected = step.get("expected", value)
        ui_helper.assert_value(selector=selector, expected=expected)


@CommandFactory.register(StepAction.ASSERT_HAVE_VALUES)
class AssertHaveValuesCommand(Command):
    """断言多个值命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        expected = step.get("expected_values", value)
        if isinstance(expected, str):
            # 尝试解析为JSON数组
            try:
                expected = json.loads(expected)
            except Exception:
                # 如果不是JSON，则分割字符串
                expected = expected.split(",")
        ui_helper.assert_values(selector=selector, expected=expected)
