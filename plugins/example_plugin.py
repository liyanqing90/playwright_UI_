"""示例插件"""

from typing import Dict, Any

from src.automation.commands.base_command import Command, CommandRegistry


@CommandRegistry.register(["custom_action"])
class CustomActionCommand(Command):
    """自定义动作命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> Any:
        """执行自定义动作"""
        print(f"执行自定义动作: {value}")
        # 在这里实现你的自定义逻辑
        return f"Custom action executed with value: {value}"


def plugin_init():
    """插件初始化函数"""
    print("示例插件已初始化")


def plugin_cleanup():
    """插件清理函数"""
    print("示例插件已清理")
