"""导航相关的命令"""

from typing import Dict, Any
import logging

from src.core.base_page import base_url
from src.automation.action_types import StepAction
from src.automation.commands.base_command import Command, CommandRegistry

logger = logging.getLogger(__name__)


@CommandRegistry.register(StepAction.NAVIGATE)
class NavigateCommand(Command):
    """导航命令"""

    def validate_args(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> bool:
        """验证导航参数"""
        if not ui_helper:
            logger.error("UI helper is required for navigation")
            return False
        return True

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        """执行导航命令"""
        self.before_execute(ui_helper, selector, value, step)
        
        try:
            url = base_url()
            if not value:
                value = url
            if "http" not in value:
                value = url + value
            
            logger.info(f"Navigating to: {value}")
            result = ui_helper.navigate(url=value)
            
            self.after_execute(result, ui_helper, selector, value, step)
            return result
            
        except Exception as e:
            self.on_error(e, ui_helper, selector, value, step)
            raise


@CommandRegistry.register(StepAction.REFRESH)
class RefreshCommand(Command):
    """刷新页面命令"""

    def validate_args(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> bool:
        """验证刷新参数"""
        if not ui_helper:
            logger.error("UI helper is required for refresh")
            return False
        return True

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        """执行刷新命令"""
        self.before_execute(ui_helper, selector, value, step)
        
        try:
            logger.info("Refreshing page")
            result = ui_helper.refresh()
            
            self.after_execute(result, ui_helper, selector, value, step)
            return result
            
        except Exception as e:
            self.on_error(e, ui_helper, selector, value, step)
            raise


@CommandRegistry.register(StepAction.PAUSE)
class PauseCommand(Command):
    """暂停命令"""

    def validate_args(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> bool:
        """验证暂停参数"""
        if not ui_helper:
            logger.error("UI helper is required for pause")
            return False
        return True

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        """执行暂停命令"""
        self.before_execute(ui_helper, selector, value, step)
        
        try:
            logger.info("Pausing execution")
            result = ui_helper.pause()
            
            self.after_execute(result, ui_helper, selector, value, step)
            return result
            
        except Exception as e:
            self.on_error(e, ui_helper, selector, value, step)
            raise
