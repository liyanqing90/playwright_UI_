"""统一配置管理模块

本模块提供统一的配置管理功能，支持多种配置文件格式和环境变量。
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

from utils.yaml_handler import YamlHandler
from .exceptions import ConfigurationError


@dataclass
class ConfigSchema:
    """配置模式定义"""

    name: str
    file_path: str
    required_keys: List[str] = field(default_factory=list)
    optional_keys: List[str] = field(default_factory=list)
    default_values: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """统一配置管理器

    提供统一的配置文件加载、验证和访问功能。
    支持 YAML、JSON 格式的配置文件，以及环境变量覆盖。
    """

    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """初始化配置管理器

        Args:
            config_dir: 配置文件目录，默认为项目根目录下的 config 文件夹
        """
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._schemas: Dict[str, ConfigSchema] = {}
        self._env_prefix = "PLAYWRIGHT_UI_"

        # 注册默认配置模式
        self._register_default_schemas()

        # 加载所有配置
        self._load_all_configs()

    def _register_default_schemas(self):
        """注册默认配置模式"""
        schemas = [
            ConfigSchema(
                name="env",
                file_path="env_config.yaml",
                required_keys=["base_url", "browser"],
                optional_keys=["headless", "timeout", "viewport"],
                default_values={
                    "headless": True,
                    "timeout": 30000,
                    "viewport": {"width": 1920, "height": 1080},
                },
            ),
            ConfigSchema(
                name="test",
                file_path="test_config.yaml",
                required_keys=["default_timeout"],
                optional_keys=[
                    "retry_count",
                    "parallel_workers",
                    "screenshot_on_failure",
                ],
                default_values={
                    "retry_count": 3,
                    "parallel_workers": 1,
                    "screenshot_on_failure": True,
                },
            ),
            ConfigSchema(
                name="performance",
                file_path="performance_config.yaml",
                optional_keys=["enable_monitoring", "metrics_collection", "thresholds"],
                default_values={
                    "enable_monitoring": False,
                    "metrics_collection": ["timing", "memory"],
                    "thresholds": {"page_load_time": 5000, "element_wait_time": 10000},
                },
            ),
        ]

        for schema in schemas:
            self._schemas[schema.name] = schema

    def register_schema(self, schema: ConfigSchema):
        """注册新的配置模式

        Args:
            schema: 配置模式定义
        """
        self._schemas[schema.name] = schema
        # 重新加载该配置
        self._load_config(schema.name)

    def _load_all_configs(self):
        """加载所有注册的配置"""
        for config_name in self._schemas.keys():
            self._load_config(config_name)

    def _load_config(self, config_name: str):
        """加载指定配置

        Args:
            config_name: 配置名称
        """
        if config_name not in self._schemas:
            raise ConfigurationError(
                config_key=config_name,
                config_file="schema registry",
                expected_type="registered schema",
            )

        schema = self._schemas[config_name]
        config_path = self.config_dir / schema.file_path

        # 加载配置文件
        config_data = {}
        if config_path.exists():
            try:
                if config_path.suffix.lower() in [".yaml", ".yml"]:
                    config_data = YamlHandler.load_yaml(config_path) or {}
                elif config_path.suffix.lower() == ".json":
                    with open(config_path, "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                else:
                    raise ConfigurationError(
                        config_key="file_format",
                        config_file=str(config_path),
                        expected_type="yaml or json",
                    )
            except Exception as e:
                raise ConfigurationError(
                    config_key="file_loading",
                    config_file=str(config_path),
                    expected_type=f"valid file: {str(e)}",
                )

        # 应用默认值
        for key, default_value in schema.default_values.items():
            if key not in config_data:
                config_data[key] = default_value

        # 应用环境变量覆盖
        config_data = self._apply_env_overrides(config_name, config_data)

        # 验证必需的配置项
        self._validate_config(config_name, config_data, schema)

        # 存储配置
        self._configs[config_name] = config_data

    def _apply_env_overrides(
        self, config_name: str, config_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用环境变量覆盖

        Args:
            config_name: 配置名称
            config_data: 原始配置数据

        Returns:
            应用环境变量后的配置数据
        """
        result = config_data.copy()

        # 遍历环境变量，查找匹配的配置项
        env_prefix = f"{self._env_prefix}{config_name.upper()}_"

        for env_key, env_value in os.environ.items():
            if env_key.startswith(env_prefix):
                # 提取配置键名
                config_key = env_key[len(env_prefix) :].lower()

                # 尝试转换环境变量值的类型
                converted_value = self._convert_env_value(env_value)
                result[config_key] = converted_value

        return result

    def _convert_env_value(self, value: str) -> Any:
        """转换环境变量值的类型

        Args:
            value: 环境变量字符串值

        Returns:
            转换后的值
        """
        # 尝试转换为布尔值
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # 尝试转换为数字
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # 尝试转换为 JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass

        # 返回原始字符串
        return value

    def _validate_config(
        self, config_name: str, config_data: Dict[str, Any], schema: ConfigSchema
    ):
        """验证配置数据

        Args:
            config_name: 配置名称
            config_data: 配置数据
            schema: 配置模式
        """
        # 检查必需的配置项
        for required_key in schema.required_keys:
            if required_key not in config_data:
                raise ConfigurationError(
                    config_key=required_key,
                    config_file=schema.file_path,
                    expected_type="required configuration",
                )

    def get_config(self, config_type: str) -> Dict[str, Any]:
        """获取指定类型的完整配置

        Args:
            config_type: 配置类型

        Returns:
            配置字典
        """
        if config_type not in self._configs:
            raise ConfigurationError(
                config_key=config_type,
                config_file="config registry",
                expected_type="registered config type",
            )

        return self._configs[config_type].copy()

    def get_value(self, config_type: str, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            config_type: 配置类型
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        config = self.get_config(config_type)
        return config.get(key, default)

    def set_value(self, config_type: str, key: str, value: Any):
        """设置配置值（运行时）

        Args:
            config_type: 配置类型
            key: 配置键
            value: 配置值
        """
        if config_type not in self._configs:
            self._configs[config_type] = {}

        self._configs[config_type][key] = value

    def reload_config(self, config_type: Optional[str] = None):
        """重新加载配置

        Args:
            config_type: 指定配置类型，None 表示重新加载所有配置
        """
        if config_type:
            self._load_config(config_type)
        else:
            self._load_all_configs()

    def get_available_configs(self) -> List[str]:
        """获取可用的配置类型列表

        Returns:
            配置类型列表
        """
        return list(self._schemas.keys())

    def export_config(
        self, config_type: str, output_path: Optional[Union[str, Path]] = None
    ) -> str:
        """导出配置到文件

        Args:
            config_type: 配置类型
            output_path: 输出文件路径，None 表示返回 YAML 字符串

        Returns:
            YAML 格式的配置字符串
        """
        config = self.get_config(config_type)
        yaml_content = YamlHandler.dump_yaml(config)

        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(yaml_content)

        return yaml_content


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例

    Returns:
        配置管理器实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config(config_type: str) -> Dict[str, Any]:
    """获取配置的便捷函数

    Args:
        config_type: 配置类型

    Returns:
        配置字典
    """
    return get_config_manager().get_config(config_type)


def get_config_value(config_type: str, key: str, default: Any = None) -> Any:
    """获取配置值的便捷函数

    Args:
        config_type: 配置类型
        key: 配置键
        default: 默认值

    Returns:
        配置值
    """
    return get_config_manager().get_value(config_type, key, default)
