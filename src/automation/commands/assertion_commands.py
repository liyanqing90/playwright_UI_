"""
断言相关的命令
"""

import json
from typing import Dict, Any

from src.automation.action_types import StepAction
from src.automation.commands.base_command import Command, CommandFactory
from src.automation.expression_evaluator import evaluate_math_expression
from utils.logger import logger


@CommandFactory.register(StepAction.ASSERT_TEXT)
class AssertTextCommand(Command):
    """断言文本命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        expected = step.get("expected", value)

        if expected is None:
            from utils.logger import logger

            # 检查原始值是否包含变量引用
            original_value = step.get("text", value)
            if (
                original_value
                and isinstance(original_value, str)
                and ("${" in original_value or "$<" in original_value)
            ):
                error_msg = (
                    f"断言失败: {selector} - 变量替换失败，原始值: {original_value}"
                )
                logger.error(error_msg)
                raise AssertionError(error_msg)
            else:
                logger.warning(f"断言跳过: {selector} - 期望值为None")
                return

        ui_helper.assert_text(selector=selector, expected=expected)

    def _build_step_description(self, *args, **kwargs) -> str:
        """构建断言文本的步骤描述"""
        if len(args) >= 4:
            selector = args[1]
            step = args[3]
            expected = step.get("expected", args[2] if len(args) > 2 else None)
            return f"断言元素 {selector} 的文本为: {expected}"
        return "断言文本"


@CommandFactory.register(StepAction.HARD_ASSERT_TEXT)
class HardAssertTextCommand(Command):
    """硬断言文本命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        expected = step.get("expected", value)

        if expected is None:
            # 检查原始值是否包含变量引用
            original_value = step.get("text", value)
            if (
                original_value
                and isinstance(original_value, str)
                and ("${" in original_value or "$<" in original_value)
            ):
                error_msg = (
                    f"断言失败: {selector} - 变量替换失败，原始值: {original_value}"
                )
                logger.error(error_msg)
                raise AssertionError(error_msg)
            else:
                logger.warning(f"断言跳过: {selector} - 期望值为None")
                return

        ui_helper.hard_assert_text(selector=selector, expected=expected)


@CommandFactory.register(StepAction.ASSERT_TEXT_CONTAINS)
class AssertTextContainsCommand(Command):
    """断言文本包含命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        text = step.get("expected", str(value))
        ui_helper.assert_text_contains(selector=selector, text=text)

    def _build_step_description(self, *args, **kwargs) -> str:
        """构建断言文本包含的步骤描述"""
        if len(args) >= 4:
            selector = args[1]
            step = args[3]
            text = step.get("expected", str(args[2]) if len(args) > 2 else "")
            return f"断言元素 {selector} 的文本包含: {text}"
        return "断言文本包含"


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
        url_part = step.get("expected", value)
        ui_helper.assert_url_contains(url_part=url_part)


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

        if expression:
            try:
                expected = evaluate_math_expression(
                    expression, ui_helper.variable_manager
                )

                logger.info(f"计算表达式: {expression} = {expected}")
            except Exception as e:

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

    def _build_step_description(self, *args, **kwargs) -> str:
        """构建断言可见的步骤描述"""
        if len(args) >= 2:
            selector = args[1]
            return f"断言元素 {selector} 可见"
        return "断言元素可见"


@CommandFactory.register(StepAction.ASSERT_BE_HIDDEN)
class AssertBeHiddenCommand(Command):
    """断言隐藏命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.assert_be_hidden(selector=selector)

    def _build_step_description(self, *args, **kwargs) -> str:
        """构建断言隐藏的步骤描述"""
        if len(args) >= 2:
            selector = args[1]
            return f"断言元素 {selector} 隐藏"
        return "断言元素隐藏"


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
                expected = expected.split(",")
        ui_helper.assert_values(selector=selector, expected=expected)
