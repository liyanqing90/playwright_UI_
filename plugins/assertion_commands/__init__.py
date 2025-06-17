"""断言命令插件

提供增强的断言功能，包括软断言、硬断言、条件断言、批量断言等。
支持多种断言类型和自定义断言逻辑。
"""

from .plugin import AssertionCommandsPlugin

__version__ = "1.0.0"
__author__ = "Playwright UI Framework"
__description__ = "增强的断言命令插件，提供多种断言类型和自定义断言功能"

__all__ = ["AssertionCommandsPlugin"]
