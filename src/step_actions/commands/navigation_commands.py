"""
导航相关的命令
"""

from typing import Dict, Any

from page_objects.base_page import base_url
from src.step_actions.action_types import StepAction
from src.step_actions.commands.base_command import Command, CommandFactory


@CommandFactory.register(StepAction.NAVIGATE)
class NavigateCommand(Command):
    """导航命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        url = base_url()
        if not value:
            value = url
        if "http" not in value:
            value = url + value
        ui_helper.navigate(url=value)


@CommandFactory.register(StepAction.REFRESH)
class RefreshCommand(Command):
    """刷新页面命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.refresh()


@CommandFactory.register(StepAction.PAUSE)
class PauseCommand(Command):
    """暂停命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.pause()
