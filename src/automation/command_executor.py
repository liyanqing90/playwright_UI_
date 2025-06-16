"""
使用命令模式的步骤执行器
"""

from typing import Dict, Any

from src.automation.commands.base_command import CommandFactory
from utils.logger import logger


def execute_action_with_command(
    ui_helper,
    action: str,
    selector: str,
    value: Any = None,
    step: Dict[str, Any] = None,
) -> None:
    """
    使用命令模式执行具体操作

    Args:
        ui_helper: UI操作帮助类
        action: 操作类型
        selector: 元素选择器
        value: 操作值
        step: 步骤定义
    """
    action = action.lower()

    command = CommandFactory.get_command(action)

    if command:
        try:
            command.execute(ui_helper, selector, value, step)
        except Exception as e:
            setattr(e, "_logged", True)
            raise
    else:
        logger.error(f"不支持的操作类型: {action}")
        raise ValueError(f"不支持的操作类型: {action}")
