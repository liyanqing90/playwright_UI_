"""
交互相关的命令
"""
from typing import Dict, Any

from constants import DEFAULT_TYPE_DELAY
from src.step_actions.action_types import StepAction
from src.step_actions.commands.base_command import Command, CommandFactory


@CommandFactory.register(StepAction.CLICK)
class ClickCommand(Command):
    """点击命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        ui_helper.click(selector)


@CommandFactory.register(StepAction.FILL)
class FillCommand(Command):
    """填充命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        ui_helper.fill(selector, value)


@CommandFactory.register(StepAction.PRESS_KEY)
class PressKeyCommand(Command):
    """按键命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        ui_helper.press_key(selector, step.get("key", value))


@CommandFactory.register(StepAction.TYPE)
class TypeCommand(Command):
    """模拟输入命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        delay = int(step.get("delay", DEFAULT_TYPE_DELAY))
        ui_helper.type(selector, value, delay)


@CommandFactory.register(StepAction.CLEAR)
class ClearCommand(Command):
    """清空命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        ui_helper.clear(selector)


@CommandFactory.register(StepAction.HOVER)
class HoverCommand(Command):
    """悬停命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        ui_helper.hover(selector)


@CommandFactory.register(StepAction.DOUBLE_CLICK)
class DoubleClickCommand(Command):
    """双击命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        ui_helper.double_click(selector)


@CommandFactory.register(StepAction.RIGHT_CLICK)
class RightClickCommand(Command):
    """右键点击命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        ui_helper.right_click(selector)


@CommandFactory.register(StepAction.SELECT)
class SelectCommand(Command):
    """选择命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        ui_helper.select_option(selector, value)


@CommandFactory.register(StepAction.UPLOAD)
class UploadCommand(Command):
    """上传文件命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        ui_helper.upload_file(selector, value)
