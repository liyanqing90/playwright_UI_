"""命令配置管理器"""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from utils.logger import logger


@dataclass
class CommandConfig:
    """单个命令的配置"""

    name: str
    enabled: bool = True
    timeout: float = 30.0
    retry_count: int = 3
    retry_delay: float = 1.0
    priority: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    custom_settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommandConfig":
        """从字典创建"""
        return cls(**data)


@dataclass
class GlobalConfig:
    """全局配置"""

    default_timeout: float = 30.0
    default_retry_count: int = 3
    default_retry_delay: float = 1.0
    max_concurrent_commands: int = 10
    enable_monitoring: bool = True
    enable_caching: bool = True
    cache_ttl: int = 3600
    log_level: str = "INFO"
    plugin_directories: List[str] = field(default_factory=list)
    auto_discovery_enabled: bool = True
    auto_discovery_paths: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GlobalConfig":
        """从字典创建"""
        return cls(**data)


class CommandConfigManager:
    """命令配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_file()
        self.global_config = GlobalConfig()
        self.command_configs: Dict[str, CommandConfig] = {}
        self._load_config()

    def _get_default_config_file(self) -> str:
        """获取默认配置文件路径"""
        # 尝试从环境变量获取
        config_path = os.getenv("COMMAND_CONFIG_FILE")
        if config_path and os.path.exists(config_path):
            return config_path

        # 使用项目根目录下的配置文件
        project_root = Path(__file__).parent.parent.parent.parent
        config_file = project_root / "config" / "commands.json"

        # 如果配置目录不存在，创建它
        config_file.parent.mkdir(parents=True, exist_ok=True)

        return str(config_file)

    def _load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 加载全局配置
                if "global" in data:
                    self.global_config = GlobalConfig.from_dict(data["global"])

                # 加载命令配置
                if "commands" in data:
                    for name, config_data in data["commands"].items():
                        config_data["name"] = name
                        self.command_configs[name] = CommandConfig.from_dict(
                            config_data
                        )

                logger.info(f"Loaded configuration from {self.config_file}")
            else:
                # 创建默认配置文件
                self._create_default_config()
                logger.info(f"Created default configuration at {self.config_file}")

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # 使用默认配置
            self.global_config = GlobalConfig()
            self.command_configs = {}

    def _create_default_config(self):
        """创建默认配置文件"""
        default_config = {
            "global": self.global_config.to_dict(),
            "commands": {
                "navigate": {
                    "enabled": True,
                    "timeout": 30.0,
                    "retry_count": 3,
                    "retry_delay": 1.0,
                    "priority": 1,
                    "tags": ["navigation", "basic"],
                    "metadata": {
                        "description": "Navigate to a URL",
                        "category": "navigation",
                    },
                },
                "click": {
                    "enabled": True,
                    "timeout": 10.0,
                    "retry_count": 2,
                    "retry_delay": 0.5,
                    "priority": 1,
                    "tags": ["interaction", "basic"],
                    "metadata": {
                        "description": "Click an element",
                        "category": "interaction",
                    },
                },
                "type": {
                    "enabled": True,
                    "timeout": 15.0,
                    "retry_count": 2,
                    "retry_delay": 0.5,
                    "priority": 1,
                    "tags": ["interaction", "input"],
                    "metadata": {
                        "description": "Type text into an element",
                        "category": "interaction",
                    },
                },
            },
        }

        self.save_config(default_config)

    def save_config(self, config_data: Optional[Dict[str, Any]] = None):
        """保存配置"""
        try:
            if config_data is None:
                config_data = {
                    "global": self.global_config.to_dict(),
                    "commands": {
                        name: config.to_dict()
                        for name, config in self.command_configs.items()
                    },
                }

            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuration saved to {self.config_file}")

        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise

    def get_global_config(self) -> GlobalConfig:
        """获取全局配置"""
        return self.global_config

    def update_global_config(self, **kwargs):
        """更新全局配置"""
        for key, value in kwargs.items():
            if hasattr(self.global_config, key):
                setattr(self.global_config, key, value)
            else:
                logger.warning(f"Unknown global config key: {key}")

        self.save_config()
        logger.info(f"Updated global configuration: {kwargs}")

    def get_command_config(self, command_name: str) -> CommandConfig:
        """获取命令配置"""
        if command_name in self.command_configs:
            return self.command_configs[command_name]

        # 返回默认配置
        default_config = CommandConfig(
            name=command_name,
            timeout=self.global_config.default_timeout,
            retry_count=self.global_config.default_retry_count,
            retry_delay=self.global_config.default_retry_delay,
        )

        # 自动保存默认配置
        self.set_command_config(command_name, default_config)

        return default_config

    def set_command_config(
        self, command_name: str, config: Union[CommandConfig, Dict[str, Any]]
    ):
        """设置命令配置"""
        if isinstance(config, dict):
            config["name"] = command_name
            config = CommandConfig.from_dict(config)

        self.command_configs[command_name] = config
        self.save_config()
        logger.info(f"Updated configuration for command: {command_name}")

    def update_command_config(self, command_name: str, **kwargs):
        """更新命令配置"""
        config = self.get_command_config(command_name)

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                logger.warning(f"Unknown command config key: {key}")

        self.command_configs[command_name] = config
        self.save_config()
        logger.info(f"Updated configuration for command {command_name}: {kwargs}")

    def remove_command_config(self, command_name: str):
        """移除命令配置"""
        if command_name in self.command_configs:
            del self.command_configs[command_name]
            self.save_config()
            logger.info(f"Removed configuration for command: {command_name}")

    def get_commands_by_tag(self, tag: str) -> List[str]:
        """根据标签获取命令列表"""
        return [
            name for name, config in self.command_configs.items() if tag in config.tags
        ]

    def get_enabled_commands(self) -> List[str]:
        """获取启用的命令列表"""
        return [name for name, config in self.command_configs.items() if config.enabled]

    def get_disabled_commands(self) -> List[str]:
        """获取禁用的命令列表"""
        return [
            name for name, config in self.command_configs.items() if not config.enabled
        ]

    def enable_command(self, command_name: str):
        """启用命令"""
        self.update_command_config(command_name, enabled=True)

    def disable_command(self, command_name: str):
        """禁用命令"""
        self.update_command_config(command_name, enabled=False)

    def get_commands_by_priority(self, min_priority: int = 0) -> List[str]:
        """根据优先级获取命令列表"""
        commands = [
            (name, config.priority)
            for name, config in self.command_configs.items()
            if config.priority >= min_priority
        ]
        commands.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in commands]

    def export_config(self, file_path: str):
        """导出配置到文件"""
        config_data = {
            "global": self.global_config.to_dict(),
            "commands": {
                name: config.to_dict() for name, config in self.command_configs.items()
            },
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Configuration exported to {file_path}")

    def import_config(self, file_path: str, merge: bool = True):
        """从文件导入配置"""
        with open(file_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        if not merge:
            # 完全替换
            self.command_configs.clear()

        # 导入全局配置
        if "global" in config_data:
            if merge:
                # 合并全局配置
                for key, value in config_data["global"].items():
                    if hasattr(self.global_config, key):
                        setattr(self.global_config, key, value)
            else:
                self.global_config = GlobalConfig.from_dict(config_data["global"])

        # 导入命令配置
        if "commands" in config_data:
            for name, config_dict in config_data["commands"].items():
                config_dict["name"] = name
                self.command_configs[name] = CommandConfig.from_dict(config_dict)

        self.save_config()
        logger.info(f"Configuration imported from {file_path} (merge={merge})")

    def validate_config(self) -> List[str]:
        """验证配置"""
        errors = []

        # 验证全局配置
        if self.global_config.default_timeout <= 0:
            errors.append("Global default_timeout must be positive")

        if self.global_config.default_retry_count < 0:
            errors.append("Global default_retry_count must be non-negative")

        if self.global_config.max_concurrent_commands <= 0:
            errors.append("Global max_concurrent_commands must be positive")

        # 验证命令配置
        for name, config in self.command_configs.items():
            if config.timeout <= 0:
                errors.append(f"Command {name}: timeout must be positive")

            if config.retry_count < 0:
                errors.append(f"Command {name}: retry_count must be non-negative")

            if config.retry_delay < 0:
                errors.append(f"Command {name}: retry_delay must be non-negative")

        return errors

    def reset_to_defaults(self):
        """重置为默认配置"""
        self.global_config = GlobalConfig()
        self.command_configs.clear()
        self._create_default_config()
        logger.info("Configuration reset to defaults")


# 全局配置管理器实例
config_manager = CommandConfigManager()
