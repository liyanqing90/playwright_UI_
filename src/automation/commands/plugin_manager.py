"""插件系统管理器"""

import json
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .base_command import Command, CommandRegistry
import logging

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    description: str
    author: str
    commands: List[str]
    dependencies: List[str]
    enabled: bool = True
    path: Optional[Path] = None


class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugin_dir: Path = None):
        self.plugin_dir = plugin_dir or Path("plugins")
        self.plugins: Dict[str, PluginInfo] = {}
        self.loaded_plugins: Dict[str, Any] = {}
        
        # 确保插件目录存在
        self.plugin_dir.mkdir(exist_ok=True)
        
        # 创建示例插件配置
        self._create_example_plugin_config()
    
    def _create_example_plugin_config(self):
        """创建示例插件配置文件"""
        example_config = {
            "name": "example_plugin",
            "version": "1.0.0",
            "description": "示例插件",
            "author": "Plugin Developer",
            "commands": ["custom_action"],
            "dependencies": [],
            "enabled": False,
            "entry_point": "example_plugin.py"
        }
        
        config_file = self.plugin_dir / "example_plugin.json"
        if not config_file.exists():
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(example_config, f, indent=2, ensure_ascii=False)
        
        # 创建示例插件代码
        example_plugin_file = self.plugin_dir / "example_plugin.py"
        if not example_plugin_file.exists():
            example_code = '''"""示例插件"""

from src.automation.commands.base_command import Command, CommandRegistry
from typing import Dict, Any


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
'''
            with open(example_plugin_file, 'w', encoding='utf-8') as f:
                f.write(example_code)
    
    def discover_plugins(self) -> List[PluginInfo]:
        """发现插件"""
        discovered = []
        
        for config_file in self.plugin_dir.glob("*.json"):
            try:
                plugin_info = self._load_plugin_config(config_file)
                if plugin_info:
                    discovered.append(plugin_info)
                    self.plugins[plugin_info.name] = plugin_info
            except Exception as e:
                logger.error(f"Failed to load plugin config {config_file}: {e}")
        
        logger.info(f"Discovered {len(discovered)} plugins")
        return discovered
    
    def _load_plugin_config(self, config_file: Path) -> Optional[PluginInfo]:
        """加载插件配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            plugin_info = PluginInfo(
                name=config['name'],
                version=config['version'],
                description=config['description'],
                author=config['author'],
                commands=config['commands'],
                dependencies=config.get('dependencies', []),
                enabled=config.get('enabled', True),
                path=self.plugin_dir / config.get('entry_point', f"{config['name']}.py")
            )
            
            return plugin_info
            
        except Exception as e:
            logger.error(f"Failed to parse plugin config {config_file}: {e}")
            return None
    
    def load_plugin(self, plugin_name: str) -> bool:
        """加载插件"""
        if plugin_name not in self.plugins:
            logger.error(f"Plugin not found: {plugin_name}")
            return False
        
        plugin_info = self.plugins[plugin_name]
        
        if not plugin_info.enabled:
            logger.warning(f"Plugin {plugin_name} is disabled")
            return False
        
        if plugin_name in self.loaded_plugins:
            logger.warning(f"Plugin {plugin_name} is already loaded")
            return True
        
        try:
            # 检查依赖
            if not self._check_dependencies(plugin_info):
                logger.error(f"Plugin {plugin_name} dependencies not satisfied")
                return False
            
            # 加载插件模块
            module = self._load_plugin_module(plugin_info)
            if not module:
                return False
            
            # 调用插件初始化函数
            if hasattr(module, 'plugin_init'):
                module.plugin_init()
            
            self.loaded_plugins[plugin_name] = module
            logger.info(f"Successfully loaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return False
    
    def _check_dependencies(self, plugin_info: PluginInfo) -> bool:
        """检查插件依赖"""
        for dep in plugin_info.dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                logger.error(f"Missing dependency: {dep}")
                return False
        return True
    
    def _load_plugin_module(self, plugin_info: PluginInfo):
        """加载插件模块"""
        if not plugin_info.path or not plugin_info.path.exists():
            logger.error(f"Plugin file not found: {plugin_info.path}")
            return None
        
        try:
            spec = importlib.util.spec_from_file_location(
                plugin_info.name, plugin_info.path
            )
            if not spec or not spec.loader:
                logger.error(f"Failed to create spec for plugin: {plugin_info.name}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            return module
            
        except Exception as e:
            logger.error(f"Failed to load plugin module {plugin_info.path}: {e}")
            return None
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        if plugin_name not in self.loaded_plugins:
            logger.warning(f"Plugin {plugin_name} is not loaded")
            return False
        
        try:
            module = self.loaded_plugins[plugin_name]
            
            # 调用插件清理函数
            if hasattr(module, 'plugin_cleanup'):
                module.plugin_cleanup()
            
            # 注销插件注册的命令
            if plugin_name in self.plugins:
                plugin_info = self.plugins[plugin_name]
                for command in plugin_info.commands:
                    CommandRegistry.unregister(command)
            
            del self.loaded_plugins[plugin_name]
            logger.info(f"Successfully unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False
    
    def load_all_plugins(self) -> int:
        """加载所有启用的插件"""
        self.discover_plugins()
        loaded_count = 0
        
        for plugin_name, plugin_info in self.plugins.items():
            if plugin_info.enabled and self.load_plugin(plugin_name):
                loaded_count += 1
        
        logger.info(f"Loaded {loaded_count} plugins")
        return loaded_count
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        if plugin_name not in self.plugins:
            logger.error(f"Plugin not found: {plugin_name}")
            return False
        
        self.plugins[plugin_name].enabled = True
        self._save_plugin_config(plugin_name)
        logger.info(f"Enabled plugin: {plugin_name}")
        return True
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        if plugin_name not in self.plugins:
            logger.error(f"Plugin not found: {plugin_name}")
            return False
        
        # 如果插件已加载，先卸载
        if plugin_name in self.loaded_plugins:
            self.unload_plugin(plugin_name)
        
        self.plugins[plugin_name].enabled = False
        self._save_plugin_config(plugin_name)
        logger.info(f"Disabled plugin: {plugin_name}")
        return True
    
    def _save_plugin_config(self, plugin_name: str):
        """保存插件配置"""
        if plugin_name not in self.plugins:
            return
        
        plugin_info = self.plugins[plugin_name]
        config_file = self.plugin_dir / f"{plugin_name}.json"
        
        config = {
            "name": plugin_info.name,
            "version": plugin_info.version,
            "description": plugin_info.description,
            "author": plugin_info.author,
            "commands": plugin_info.commands,
            "dependencies": plugin_info.dependencies,
            "enabled": plugin_info.enabled,
            "entry_point": plugin_info.path.name if plugin_info.path else f"{plugin_name}.py"
        }
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save plugin config {config_file}: {e}")
    
    def list_plugins(self) -> Dict[str, PluginInfo]:
        """列出所有插件"""
        return self.plugins.copy()
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        return self.plugins.get(plugin_name)
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """检查插件是否已加载"""
        return plugin_name in self.loaded_plugins
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """重新加载插件"""
        if self.is_plugin_loaded(plugin_name):
            self.unload_plugin(plugin_name)
        return self.load_plugin(plugin_name)


# 全局插件管理器实例
plugin_manager = PluginManager()