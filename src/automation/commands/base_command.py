"""基础命令类和命令注册系统"""

import asyncio
import importlib
import inspect
import pkgutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Type, Any, Optional, List, Set

import allure
from utils.logger import logger
from .command_config import config_manager, CommandConfig
from .command_monitor import command_monitor


class Command(ABC):
    """命令基类"""

    def __init__(self):
        self.config: CommandConfig = config_manager.get_command_config(
            self.__class__.__name__
        )
        self.name = self.__class__.__name__

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """执行命令"""
        pass

    def execute_with_monitoring(self, *args, **kwargs) -> Any:
        """带监控的执行命令"""
        with command_monitor.monitor_command(self.name):
            return self.execute(*args, **kwargs)

    async def execute_async(self, *args, **kwargs) -> Any:
        """异步执行命令"""
        if asyncio.iscoroutinefunction(self.execute):
            return await self.execute(*args, **kwargs)
        else:
            # 在线程池中执行同步命令
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.execute, *args, **kwargs)

    def is_enabled(self) -> bool:
        """检查命令是否启用"""
        return self.config.enabled

    def get_timeout(self) -> float:
        """获取命令超时时间"""
        return self.config.timeout

    def get_retry_config(self) -> tuple[int, float]:
        """获取重试配置"""
        return self.config.retry_count, self.config.retry_delay

    def validate_args(self, *args, **kwargs) -> bool:
        """验证参数（子类可重写）"""
        return True

    def before_execute(self, *args, **kwargs):
        """执行前钩子（子类可重写）"""
        pass

    def after_execute(self, result: Any, *args, **kwargs):
        """执行后钩子（子类可重写）"""
        pass

    def on_error(self, error: Exception, *args, **kwargs):
        """错误处理钩子（子类可重写）"""
        logger.error(f"Error in command {self.name}: {error}")
        raise error


class CommandRegistry:
    """命令注册表 - 支持自动发现和插件机制"""

    _commands: Dict[str, Type[Command]] = {}
    _loaded_modules: Set[str] = set()
    _plugin_paths: List[Path] = []

    @classmethod
    def register(cls, action_types):
        """
        注册命令的装饰器

        Args:
            action_types: 操作类型列表或单个操作类型
        """
        # 如果是字符串，转换为列表
        if isinstance(action_types, str):
            action_types = [action_types]
        # 如果是列表（如StepAction.NAVIGATE），直接使用
        elif isinstance(action_types, list):
            action_types = action_types
        else:
            # 其他类型转换为列表
            action_types = [action_types]

        def decorator(command_class: Type[Command]):
            for action_type in action_types:
                action_key = (
                    action_type.lower()
                    if hasattr(action_type, "lower")
                    else str(action_type).lower()
                )
                cls._commands[action_key] = command_class
                # logger.debug(f"Registered command: {action_key} -> {command_class.__name__}")
            return command_class

        return decorator

    @classmethod
    def auto_discover_commands(cls, package_name: str = None):
        """
        自动发现并注册命令

        Args:
            package_name: 包名，默认为当前包
        """
        if package_name is None:
            package_name = __package__

        if package_name in cls._loaded_modules:
            return

        try:
            # 获取包路径
            package = importlib.import_module(package_name)
            package_path = package.__path__

            # 遍历包中的所有模块
            for importer, modname, ispkg in pkgutil.iter_modules(package_path):
                if (
                    not ispkg
                    and modname != "base_command"
                    and not modname.startswith("_")
                ):
                    full_module_name = f"{package_name}.{modname}"
                    try:
                        # 动态导入模块，触发装饰器注册
                        importlib.import_module(full_module_name)
                        # logger.debug(f"Auto-discovered module: {full_module_name}")
                    except Exception as e:
                        logger.warning(
                            f"Failed to import module {full_module_name}: {e}"
                        )

            cls._loaded_modules.add(package_name)
            logger.info(f"Auto-discovery completed for package: {package_name}")

        except Exception as e:
            logger.error(f"Failed to auto-discover commands in {package_name}: {e}")

    @classmethod
    def register_from_module(cls, module_name: str):
        """
        从指定模块注册命令

        Args:
            module_name: 模块名
        """
        try:
            module = importlib.import_module(module_name)

            # 扫描模块中的命令类
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, Command)
                    and obj != Command
                    and name.endswith("Command")
                ):

                    # 检查是否已经通过装饰器注册
                    if not any(
                        obj == cmd_class for cmd_class in cls._commands.values()
                    ):
                        # 尝试从类名推断操作类型
                        action_type = name.replace("Command", "").lower()
                        cls._commands[action_type] = obj
                        logger.info(
                            f"Auto-registered command from module {module_name}: {action_type} -> {name}"
                        )

        except Exception as e:
            logger.error(f"Failed to register commands from module {module_name}: {e}")

    @classmethod
    def add_plugin_path(cls, path: Path):
        """
        添加插件路径

        Args:
            path: 插件目录路径
        """
        if path.exists() and path.is_dir():
            cls._plugin_paths.append(path)
            logger.info(f"Added plugin path: {path}")

    @classmethod
    def load_plugins(cls):
        """
        加载所有插件
        """
        for plugin_path in cls._plugin_paths:
            cls._load_plugins_from_path(plugin_path)

    @classmethod
    def _load_plugins_from_path(cls, path: Path):
        """
        从指定路径加载插件

        Args:
            path: 插件路径
        """
        try:
            # 查找Python文件
            for py_file in path.glob("**/*.py"):
                if py_file.name.startswith("_"):
                    continue

                # 构造模块名
                relative_path = py_file.relative_to(path)
                module_parts = list(relative_path.parts[:-1]) + [relative_path.stem]
                module_name = ".".join(module_parts)

                # 动态导入插件模块
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # 注册插件中的命令
                    cls._register_commands_from_module(module)
                    logger.info(f"Loaded plugin: {py_file}")

        except Exception as e:
            logger.error(f"Failed to load plugins from {path}: {e}")

    @classmethod
    def _register_commands_from_module(cls, module):
        """
        从模块中注册命令类

        Args:
            module: Python模块
        """
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Command) and obj != Command and hasattr(obj, "execute"):

                # 从类名推断操作类型
                action_type = name.replace("Command", "").lower()
                cls._commands[action_type] = obj
                logger.info(f"Registered plugin command: {action_type} -> {name}")

    @classmethod
    def get_command(cls, action: str) -> Optional[Command]:
        """
        获取命令实例

        Args:
            action: 操作类型

        Returns:
            命令实例或None
        """
        action_key = action.lower()
        # logger.debug(
        #     f"查找命令: {action_key}, 已注册命令: {list(cls._commands.keys())}"
        # )

        command_class = cls._commands.get(action_key)
        if command_class:
            try:
                instance = command_class()
                # 检查命令是否启用
                if not instance.is_enabled():
                    logger.warning(f"Command {action} is disabled")
                    return None
                # logger.debug(f"成功创建命令实例: {action}")
                return instance
            except Exception as e:
                logger.error(f"Failed to instantiate command {action}: {e}")
                return None

        logger.warning(
            f"Command not found: {action}, available commands: {list(cls._commands.keys())}"
        )
        return None

    @classmethod
    def list_commands(cls) -> Dict[str, Type[Command]]:
        """
        列出所有已注册的命令

        Returns:
            命令字典
        """
        return cls._commands.copy()

    @classmethod
    def unregister(cls, action: str) -> bool:
        """
        注销命令

        Args:
            action: 操作类型

        Returns:
            是否成功注销
        """
        action_key = action.lower()
        if action_key in cls._commands:
            del cls._commands[action_key]
            logger.info(f"Unregistered command: {action}")
            return True
        return False

    @classmethod
    def clear_all(cls):
        """
        清除所有注册的命令
        """
        cls._commands.clear()
        cls._loaded_modules.clear()
        logger.info("Cleared all registered commands")


# 保持向后兼容性
CommandFactory = CommandRegistry
