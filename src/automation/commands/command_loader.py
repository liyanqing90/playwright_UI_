"""命令延迟加载器"""

import importlib
from typing import Dict, Type, Optional, Set

from utils.logger import logger
from .base_command import Command, CommandRegistry


class CommandLoader:
    """命令延迟加载器 - 优化启动性能"""
    
    # 命令模块映射
    _command_modules = {
        'navigate': 'src.automation.commands.navigation_commands',
        'click': 'src.automation.commands.interaction_commands',
        'fill': 'src.automation.commands.interaction_commands',
        'type': 'src.automation.commands.interaction_commands',
        'wait': 'src.automation.commands.wait_commands',
        'assert': 'src.automation.commands.assertion_commands',
        'screenshot': 'src.automation.commands.misc_commands',
        'upload': 'src.automation.commands.file_commands',
        'download': 'src.automation.commands.file_commands',
        'network': 'src.automation.commands.network_commands',
        'storage': 'src.automation.commands.storage_commands',
        'window': 'src.automation.commands.window_commands',
    }
    
    _loaded_modules: Set[str] = set()
    _command_cache: Dict[str, Type[Command]] = {}
    
    @classmethod
    def get_command_class(cls, action_type: str) -> Optional[Type[Command]]:
        """
        获取命令类（延迟加载）
        
        Args:
            action_type: 操作类型
            
        Returns:
            命令类，如果不存在则返回None
        """
        action_key = action_type.lower()
        
        # 首先检查缓存
        if action_key in cls._command_cache:
            return cls._command_cache[action_key]
        
        # 检查已注册的命令
        registered_commands = CommandRegistry.list_commands()
        if action_key in registered_commands:
            cls._command_cache[action_key] = registered_commands[action_key]
            return registered_commands[action_key]
        
        # 确定命令所属模块并延迟加载
        module_name = cls._determine_module(action_key)
        if module_name and module_name not in cls._loaded_modules:
            try:
                # 动态导入模块
                importlib.import_module(module_name)
                cls._loaded_modules.add(module_name)
                logger.debug(f"Lazy loaded module: {module_name}")
                
                # 重新检查注册的命令
                registered_commands = CommandRegistry.list_commands()
                if action_key in registered_commands:
                    cls._command_cache[action_key] = registered_commands[action_key]
                    return registered_commands[action_key]
                    
            except Exception as e:
                logger.error(f"Failed to lazy load module {module_name}: {e}")
        
        return None
    
    @classmethod
    def _determine_module(cls, action_type: str) -> Optional[str]:
        """
        确定动作类型所属的模块
        
        Args:
            action_type: 操作类型
            
        Returns:
            模块名，如果无法确定则返回None
        """
        # 直接映射
        if action_type in cls._command_modules:
            return cls._command_modules[action_type]
        
        # 模糊匹配
        for key, module in cls._command_modules.items():
            if key in action_type or action_type in key:
                return module
        
        # 根据动作类型推断
        if any(keyword in action_type for keyword in ['wait', 'sleep', 'pause']):
            return cls._command_modules['wait']
        elif any(keyword in action_type for keyword in ['click', 'hover', 'drag']):
            return cls._command_modules['click']
        elif any(keyword in action_type for keyword in ['input', 'fill', 'type']):
            return cls._command_modules['fill']
        elif any(keyword in action_type for keyword in ['assert', 'verify', 'check']):
            return cls._command_modules['assert']
        elif any(keyword in action_type for keyword in ['file', 'upload', 'download']):
            return cls._command_modules['upload']
        elif any(keyword in action_type for keyword in ['network', 'request', 'response']):
            return cls._command_modules['network']
        elif any(keyword in action_type for keyword in ['storage', 'cookie', 'session']):
            return cls._command_modules['storage']
        elif any(keyword in action_type for keyword in ['window', 'tab', 'frame']):
            return cls._command_modules['window']
        
        return None
    
    @classmethod
    def preload_common_commands(cls):
        """
        预加载常用命令模块
        """
        common_modules = [
            'src.automation.commands.navigation_commands',
            'src.automation.commands.interaction_commands',
            'src.automation.commands.wait_commands',
        ]
        
        for module_name in common_modules:
            if module_name not in cls._loaded_modules:
                try:
                    importlib.import_module(module_name)
                    cls._loaded_modules.add(module_name)
                    logger.debug(f"Preloaded module: {module_name}")
                except Exception as e:
                    logger.warning(f"Failed to preload module {module_name}: {e}")
    
    @classmethod
    def get_loaded_modules(cls) -> Set[str]:
        """
        获取已加载的模块列表
        
        Returns:
            已加载模块集合
        """
        return cls._loaded_modules.copy()
    
    @classmethod
    def clear_cache(cls):
        """
        清除缓存
        """
        cls._command_cache.clear()
        cls._loaded_modules.clear()
        logger.info("Cleared command loader cache")
    
    @classmethod
    def add_module_mapping(cls, action_type: str, module_name: str):
        """
        添加动作类型到模块的映射
        
        Args:
            action_type: 操作类型
            module_name: 模块名
        """
        cls._command_modules[action_type.lower()] = module_name
        logger.info(f"Added module mapping: {action_type} -> {module_name}")