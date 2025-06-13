"""交互相关的命令"""

from typing import Dict, Any
import logging

from config.constants import DEFAULT_TYPE_DELAY
from src.automation.action_types import StepAction
from src.automation.commands.base_command import Command, CommandRegistry, CommandFactory

logger = logging.getLogger(__name__)


@CommandRegistry.register(StepAction.CLICK)
class ClickCommand(Command):
    """点击命令"""

    def validate_args(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> bool:
        """验证点击参数"""
        if not ui_helper:
            logger.error("UI helper is required for click")
            return False
        if not selector:
            logger.error("Selector is required for click")
            return False
        return True

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        """执行点击命令"""
        self.before_execute(ui_helper, selector, value, step)
        
        try:
            logger.info(f"Clicking element: {selector}")
            result = ui_helper.click(selector=selector)
            
            self.after_execute(result, ui_helper, selector, value, step)
            return result
            
        except Exception as e:
            self.on_error(e, ui_helper, selector, value, step)
            raise


@CommandRegistry.register(StepAction.FILL)
class FillCommand(Command):
    """填充命令"""

    def validate_args(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> bool:
        """验证填充参数"""
        if not ui_helper:
            logger.error("UI helper is required for fill")
            return False
        if not selector:
            logger.error("Selector is required for fill")
            return False
        if value is None:
            logger.error("Value is required for fill")
            return False
        return True

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        """执行填充命令"""
        self.before_execute(ui_helper, selector, value, step)
        
        try:
            logger.info(f"Filling element {selector} with value: {value}")
            result = ui_helper.fill(selector=selector, value=value)
            
            self.after_execute(result, ui_helper, selector, value, step)
            return result
            
        except Exception as e:
            self.on_error(e, ui_helper, selector, value, step)
            raise


@CommandRegistry.register(StepAction.PRESS_KEY)
class PressKeyCommand(Command):
    """按键命令"""

    def validate_args(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> bool:
        """验证按键参数"""
        if not ui_helper:
            logger.error("UI helper is required for press key")
            return False
        if not selector:
            logger.error("Selector is required for press key")
            return False
        key = step.get("key", value)
        if not key:
            logger.error("Key is required for press key")
            return False
        return True

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        """执行按键命令"""
        self.before_execute(ui_helper, selector, value, step)
        
        try:
            key = step.get("key", value)
            logger.info(f"Pressing key {key} on element: {selector}")
            result = ui_helper.press_key(selector=selector, key=key)
            
            self.after_execute(result, ui_helper, selector, value, step)
            return result
            
        except Exception as e:
            self.on_error(e, ui_helper, selector, value, step)
            raise


@CommandRegistry.register(StepAction.TYPE)
class TypeCommand(Command):
    """模拟输入命令"""

    def validate_args(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> bool:
        """验证输入参数"""
        if not ui_helper:
            logger.error("UI helper is required for type")
            return False
        if not selector:
            logger.error("Selector is required for type")
            return False
        if value is None:
            logger.error("Text value is required for type")
            return False
        return True

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        """执行输入命令"""
        self.before_execute(ui_helper, selector, value, step)
        
        try:
            delay = int(step.get("delay", DEFAULT_TYPE_DELAY))
            logger.info(f"Typing text '{value}' into element {selector} with delay {delay}ms")
            result = ui_helper.type(selector=selector, text=value, delay=delay)
            
            self.after_execute(result, ui_helper, selector, value, step)
            return result
            
        except Exception as e:
            self.on_error(e, ui_helper, selector, value, step)
            raise


@CommandFactory.register(StepAction.CLEAR)
class ClearCommand(Command):
    """清空命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.clear(selector=selector)


@CommandFactory.register(StepAction.HOVER)
class HoverCommand(Command):
    """悬停命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.hover(selector=selector)


@CommandFactory.register(StepAction.DOUBLE_CLICK)
class DoubleClickCommand(Command):
    """双击命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.double_click(selector=selector)


@CommandFactory.register(StepAction.RIGHT_CLICK)
class RightClickCommand(Command):
    """右键点击命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.right_click(selector=selector)


@CommandFactory.register(StepAction.SELECT)
class SelectCommand(Command):
    """选择命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.select_option(selector=selector, value=value)


@CommandFactory.register(StepAction.UPLOAD)
class UploadCommand(Command):
    """上传文件命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.upload_file(selector=selector, file_path=value)
