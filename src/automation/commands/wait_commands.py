"""
等待相关的命令
"""

from typing import Dict, Any

from config.constants import DEFAULT_TIMEOUT
from src.automation.action_types import StepAction
from src.automation.commands.base_command import Command, CommandFactory


@CommandFactory.register(StepAction.WAIT)
class WaitCommand(Command):
    """等待命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        # 优先使用step中的value，然后是传入的value，最后是默认值1秒
        if value:
            wait_time = int(value) * 1000
        else:
            wait_time = 1000  # 默认1秒

        from utils.logger import logger

        logger.debug(f"等待 {wait_time}ms")
        ui_helper.wait_for_timeout(timeout=wait_time)

    def _build_step_description(self, *args, **kwargs) -> str:
        """构建等待操作的步骤描述"""
        if len(args) >= 3:
            value = args[2]
            if value:
                wait_time = int(value)
                return f"等待 {wait_time} 秒"
        return "等待 1 秒"


@CommandFactory.register(StepAction.WAIT_FOR_NETWORK_IDLE)
class WaitForNetworkIdleCommand(Command):
    """等待网络空闲命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        timeout = int(step.get("timeout", DEFAULT_TIMEOUT))
        ui_helper.wait_for_network_idle(timeout=timeout)


@CommandFactory.register(StepAction.WAIT_FOR_ELEMENT_HIDDEN)
class WaitForElementHiddenCommand(Command):
    """等待元素消失命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        timeout = int(step.get("timeout", DEFAULT_TIMEOUT))
        ui_helper.wait_for_element_hidden(selector=selector, timeout=timeout)

    def _build_step_description(self, *args, **kwargs) -> str:
        """构建等待元素隐藏的步骤描述"""
        if len(args) >= 2:
            selector = args[1]
            return f"等待元素 {selector} 隐藏"
        return "等待元素隐藏"


@CommandFactory.register(StepAction.WAIT_FOR_ELEMENT_CLICKABLE)
class WaitForElementClickableCommand(Command):
    """等待元素可点击命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        timeout = int(step.get("timeout", DEFAULT_TIMEOUT))
        ui_helper.wait_for_element_clickable(selector=selector, timeout=timeout)


@CommandFactory.register(StepAction.WAIT_FOR_ELEMENT_TEXT)
class WaitForElementTextCommand(Command):
    """等待元素文本命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        timeout = int(step.get("timeout", DEFAULT_TIMEOUT))
        expected_text = step.get("expected_text", value)
        ui_helper.wait_for_element_text(
            selector=selector, expected_text=expected_text, timeout=timeout
        )


@CommandFactory.register(StepAction.WAIT_FOR_ELEMENT_COUNT)
class WaitForElementCountCommand(Command):
    """等待元素数量命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        timeout = int(step.get("timeout", DEFAULT_TIMEOUT))
        expected_count = int(step.get("expected_count", value))
        ui_helper.wait_for_element_count(
            selector=selector, expected_count=expected_count, timeout=timeout
        )


@CommandFactory.register(StepAction.WAIT_FOR_NEW_WINDOW)
class WaitForNewWindowCommand(Command):
    """等待新窗口命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        new_page = ui_helper.wait_for_new_window()
        if "variable_name" in step:
            ui_helper.store_variable(
                step["variable_name"], new_page, step.get("scope", "global")
            )
