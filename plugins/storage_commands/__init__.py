"""存储命令插件 (Storage Commands Plugin)

提供全面的数据存储和状态管理功能，包括变量存储、数据持久化、
缓存管理和状态管理等功能。

主要功能:
- 变量存储和管理
- 元素属性和文本存储
- 数据持久化
- 缓存管理
- 状态管理
- 作用域控制
- 数据序列化
- 批量操作

作者: Playwright UI Framework Team
版本: 1.0.0
创建时间: 2024-01-15
"""

from .plugin import StorageCommandsPlugin

__version__ = "1.0.0"
__author__ = "Playwright UI Framework Team"
__description__ = "存储命令插件 - 提供全面的数据存储和状态管理功能"

__all__ = ["StorageCommandsPlugin"]
