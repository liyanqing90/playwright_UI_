"""
navigation_commands - 合并的命令文件

合并了以下文件的命令:
- navigation_commands.py
- window_commands.py
"""

from typing import Dict, Any

from src.automation.action_types import StepAction
from src.automation.commands.base_command import Command, CommandFactory
from utils.logger import logger


@CommandFactory.register(StepAction.NAVIGATE)
class NavigateCommand(Command):
    """导航命令"""

    def validate_args(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> bool:
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
            # 从step参数中获取base_url，如果没有则使用value作为完整URL
            base_url_value = step.get("base_url", "") if step else ""

            if not value:
                value = base_url_value
            elif "http" not in value and base_url_value:
                # 如果value不是完整URL且有base_url，则拼接
                value = f"{base_url_value.rstrip('/')}/{value.lstrip('/')}"

            logger.info(f"Navigating to: {value}")
            result = ui_helper.navigate(url=value)

            self.after_execute(result, ui_helper, selector, value, step)
            return result

        except Exception as e:
            self.on_error(e, ui_helper, selector, value, step)
            raise

    def _build_step_description(self, *args, **kwargs) -> str:
        """构建导航操作的步骤描述"""
        if len(args) >= 3:
            value = args[2]
            return f"导航到页面: {value}"
        return "页面导航"


@CommandFactory.register(StepAction.REFRESH)
class RefreshCommand(Command):
    """刷新页面命令"""

    def validate_args(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> bool:
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


@CommandFactory.register(StepAction.PAUSE)
class PauseCommand(Command):
    """暂停命令"""

    def validate_args(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> bool:
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


class ExpectPopupCommand(Command):
    """弹出tab命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        action = step.get("real_action", "click")
        variable_name = step.get("variable_name", value)
        ui_helper.expect_popup(
            action=action, selector=selector, variable_name=variable_name
        )


@CommandFactory.register(StepAction.SWITCH_WINDOW)
class SwitchWindowCommand(Command):
    """切换窗口命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.switch_window(value=value)


@CommandFactory.register(StepAction.CLOSE_WINDOW)
class CloseWindowCommand(Command):
    """关闭窗口命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.close_window()


@CommandFactory.register(StepAction.TAB_SWITCH)
class TabSwitchCommand(Command):
    """切换标签页命令"""

    def execute(
        self, ui_helper, selector: str, value: Any, step: Dict[str, Any]
    ) -> None:
        ui_helper.switch_window(value=value)
