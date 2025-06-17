"""命令模式实现包"""

from .base_command import Command, CommandRegistry, CommandFactory

# 自动发现并注册所有命令
CommandRegistry.auto_discover_commands(__name__)

# 导出主要接口
__all__ = ["Command", "CommandRegistry", "CommandFactory"]

from .element_commands import *
from .io_commands import *
from .utility_commands import *
