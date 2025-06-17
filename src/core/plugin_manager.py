import importlib.util
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from .container import ServiceContainer
from .interfaces.plugin_interface import (
    PluginInterface,
    PluginMetadata,
    PluginStatus,
    PluginLoadError,
    PluginInitializationError,
    PluginDependencyError,
    ConfigurablePlugin,
    LifecyclePlugin,
)


class PluginManager:
    """插件管理器

    负责插件的加载、初始化、依赖管理和生命周期控制。
    实现分层架构与插件系统的职责划分。
    """

    def __init__(self, service_container: ServiceContainer, logger):
        self.service_container = service_container
        self.logger = logger
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        self.plugin_directories: List[str] = []
        self.load_order: List[str] = []

    def add_plugin_directory(self, directory: str) -> None:
        """添加插件目录

        Args:
            directory: 插件目录路径
        """
        if os.path.exists(directory) and directory not in self.plugin_directories:
            self.plugin_directories.append(directory)
            self.logger.info(f"Added plugin directory: {directory}")

    def discover_plugins(self) -> List[PluginMetadata]:
        """发现所有插件

        Returns:
            List[PluginMetadata]: 发现的插件元数据列表
        """
        discovered_plugins = []

        for directory in self.plugin_directories:
            for plugin_dir in Path(directory).iterdir():
                if plugin_dir.is_dir() and not plugin_dir.name.startswith("."):
                    metadata_file = plugin_dir / "metadata.json"
                    if metadata_file.exists():
                        try:
                            import json

                            with open(metadata_file, "r", encoding="utf-8") as f:
                                metadata_data = json.load(f)
                            metadata = PluginMetadata.from_dict(metadata_data)
                            discovered_plugins.append(metadata)
                            self.logger.debug(f"Discovered plugin: {metadata.name}")
                        except Exception as e:
                            self.logger.error(
                                f"Failed to load metadata for {plugin_dir.name}: {e}"
                            )

        return discovered_plugins

    def load_plugin(self, metadata: PluginMetadata, plugin_directory: str) -> bool:
        """加载单个插件

        Args:
            metadata: 插件元数据
            plugin_directory: 插件目录路径

        Returns:
            bool: 加载是否成功
        """
        if metadata.name in self.plugins:
            self.logger.warning(f"Plugin {metadata.name} already loaded")
            return True

        try:
            metadata.status = PluginStatus.LOADING
            start_time = time.time()

            # 构建插件文件路径
            plugin_path = Path(plugin_directory) / metadata.name / metadata.entry_point
            if not plugin_path.exists():
                raise PluginLoadError(f"Plugin file not found: {plugin_path}")

            # 动态加载插件模块
            spec = importlib.util.spec_from_file_location(
                f"plugin_{metadata.name}", plugin_path
            )
            if spec is None or spec.loader is None:
                raise PluginLoadError(
                    f"Failed to create module spec for {metadata.name}"
                )

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 获取插件类
            plugin_class = getattr(module, metadata.class_name, None)
            if plugin_class is None:
                raise PluginLoadError(f"Plugin class {metadata.class_name} not found")

            # 实例化插件
            plugin_instance = plugin_class()
            if not isinstance(plugin_instance, PluginInterface):
                raise PluginLoadError(
                    f"Plugin {metadata.name} does not implement PluginInterface"
                )

            # 记录加载信息
            metadata.load_time = time.time() - start_time
            metadata.status = PluginStatus.LOADED

            self.plugins[metadata.name] = plugin_instance
            self.plugin_metadata[metadata.name] = metadata

            self.logger.info(
                f"Successfully loaded plugin: {metadata.name} ({metadata.load_time:.3f}s)"
            )
            return True

        except Exception as e:
            metadata.status = PluginStatus.ERROR
            metadata.error_message = str(e)
            self.logger.error(f"Failed to load plugin {metadata.name}: {e}")
            return False

    def initialize_plugin(self, plugin_name: str) -> bool:
        """初始化插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 初始化是否成功
        """
        if plugin_name not in self.plugins:
            self.logger.error(f"Plugin {plugin_name} not loaded")
            return False

        try:
            plugin = self.plugins[plugin_name]
            metadata = self.plugin_metadata[plugin_name]

            metadata.status = PluginStatus.INITIALIZING

            # 检查依赖
            if not self._check_dependencies(metadata):
                raise PluginDependencyError(
                    f"Dependencies not satisfied for {plugin_name}"
                )

            # 初始化插件
            if not plugin.initialize(self.service_container):
                raise PluginInitializationError(
                    f"Plugin {plugin_name} initialization failed"
                )

            # 配置插件（如果支持）
            if isinstance(plugin, ConfigurablePlugin) and metadata.config:
                if not plugin.configure(metadata.config):
                    self.logger.warning(f"Plugin {plugin_name} configuration failed")

            metadata.status = PluginStatus.ACTIVE
            self.logger.info(f"Successfully initialized plugin: {plugin_name}")
            return True

        except Exception as e:
            metadata.status = PluginStatus.ERROR
            metadata.error_message = str(e)
            self.logger.error(f"Failed to initialize plugin {plugin_name}: {e}")
            return False

    def _check_dependencies(self, metadata: PluginMetadata) -> bool:
        """检查插件依赖

        Args:
            metadata: 插件元数据

        Returns:
            bool: 依赖是否满足
        """
        for dependency in metadata.dependencies:
            if dependency not in self.plugins:
                self.logger.error(
                    f"Dependency {dependency} not found for plugin {metadata.name}"
                )
                return False

            dep_metadata = self.plugin_metadata[dependency]
            if dep_metadata.status != PluginStatus.ACTIVE:
                self.logger.error(
                    f"Dependency {dependency} not active for plugin {metadata.name}"
                )
                return False

        return True

    def _calculate_load_order(self, plugins: List[PluginMetadata]) -> List[str]:
        """计算插件加载顺序

        Args:
            plugins: 插件元数据列表

        Returns:
            List[str]: 按依赖关系和优先级排序的插件名称列表
        """
        # 按优先级分组
        priority_groups = {}
        for plugin in plugins:
            if plugin.enabled:
                priority = plugin.priority
                if priority not in priority_groups:
                    priority_groups[priority] = []
                priority_groups[priority].append(plugin)

        load_order = []

        # 按优先级顺序处理
        for priority in sorted(priority_groups.keys(), key=lambda x: x.value):
            group_plugins = priority_groups[priority]

            # 在同一优先级内按依赖关系排序
            resolved = set()
            remaining = {p.name: p for p in group_plugins}

            while remaining:
                progress = False
                for name, plugin in list(remaining.items()):
                    # 检查依赖是否已解决
                    deps_resolved = all(
                        dep in resolved or dep in load_order
                        for dep in plugin.dependencies
                    )

                    if deps_resolved:
                        load_order.append(name)
                        resolved.add(name)
                        del remaining[name]
                        progress = True

                if not progress and remaining:
                    # 循环依赖或缺失依赖
                    self.logger.error(
                        f"Circular dependency or missing dependency detected: {list(remaining.keys())}"
                    )
                    # 强制添加剩余插件
                    load_order.extend(remaining.keys())
                    break

        return load_order

    def load_all_plugins(self) -> Dict[str, bool]:
        """加载所有插件

        Returns:
            Dict[str, bool]: 插件名称到加载结果的映射
        """
        discovered_plugins = self.discover_plugins()
        self.load_order = self._calculate_load_order(discovered_plugins)

        results = {}

        # 按计算的顺序加载和初始化插件
        for plugin_name in self.load_order:
            plugin_metadata = next(
                (p for p in discovered_plugins if p.name == plugin_name), None
            )
            if plugin_metadata is None:
                results[plugin_name] = False
                continue

            # 查找插件目录
            plugin_directory = None
            for directory in self.plugin_directories:
                plugin_path = Path(directory) / plugin_name
                if plugin_path.exists():
                    plugin_directory = directory
                    break

            if plugin_directory is None:
                self.logger.error(f"Plugin directory not found for {plugin_name}")
                results[plugin_name] = False
                continue

            # 加载插件
            load_success = self.load_plugin(plugin_metadata, plugin_directory)
            if load_success:
                # 初始化插件
                init_success = self.initialize_plugin(plugin_name)
                results[plugin_name] = init_success
            else:
                results[plugin_name] = False

        self.logger.info(
            f"Plugin loading completed. Success: {sum(results.values())}, Failed: {len(results) - sum(results.values())}"
        )
        return results

    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 卸载是否成功
        """
        if plugin_name not in self.plugins:
            self.logger.warning(f"Plugin {plugin_name} not loaded")
            return True

        try:
            plugin = self.plugins[plugin_name]
            metadata = self.plugin_metadata[plugin_name]

            metadata.status = PluginStatus.STOPPING

            # 停止插件（如果支持生命周期管理）
            if isinstance(plugin, LifecyclePlugin):
                plugin.stop()

            # 清理插件
            plugin.cleanup()

            # 从管理器中移除
            del self.plugins[plugin_name]
            del self.plugin_metadata[plugin_name]

            if plugin_name in self.load_order:
                self.load_order.remove(plugin_name)

            self.logger.info(f"Successfully unloaded plugin: {plugin_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False

    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """获取插件实例

        Args:
            plugin_name: 插件名称

        Returns:
            Optional[PluginInterface]: 插件实例，如果不存在则返回None
        """
        return self.plugins.get(plugin_name)

    def get_plugin_metadata(self, plugin_name: str) -> Optional[PluginMetadata]:
        """获取插件元数据

        Args:
            plugin_name: 插件名称

        Returns:
            Optional[PluginMetadata]: 插件元数据，如果不存在则返回None
        """
        return self.plugin_metadata.get(plugin_name)

    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """列出所有插件信息

        Returns:
            Dict[str, Dict[str, Any]]: 插件信息字典
        """
        plugin_info = {}
        for name, metadata in self.plugin_metadata.items():
            plugin_info[name] = {
                "metadata": metadata.to_dict(),
                "loaded": name in self.plugins,
                "health": (
                    self.plugins[name].get_health_status()
                    if name in self.plugins
                    else None
                ),
            }
        return plugin_info

    def get_plugins_by_status(self, status: PluginStatus) -> List[str]:
        """根据状态获取插件列表

        Args:
            status: 插件状态

        Returns:
            List[str]: 符合状态的插件名称列表
        """
        return [
            name
            for name, metadata in self.plugin_metadata.items()
            if metadata.status == status
        ]

    def restart_plugin(self, plugin_name: str) -> bool:
        """重启插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 重启是否成功
        """
        if plugin_name not in self.plugins:
            self.logger.error(f"Plugin {plugin_name} not loaded")
            return False

        plugin = self.plugins[plugin_name]

        # 如果插件支持生命周期管理，使用其重启方法
        if isinstance(plugin, LifecyclePlugin):
            return plugin.restart()

        # 否则手动重启
        if self.unload_plugin(plugin_name):
            metadata = self.get_plugin_metadata(plugin_name)
            if metadata:
                plugin_directory = None
                for directory in self.plugin_directories:
                    plugin_path = Path(directory) / plugin_name
                    if plugin_path.exists():
                        plugin_directory = directory
                        break

                if plugin_directory:
                    return self.load_plugin(
                        metadata, plugin_directory
                    ) and self.initialize_plugin(plugin_name)

        return False

    def shutdown(self) -> None:
        """关闭插件管理器，卸载所有插件"""
        self.logger.info("Shutting down plugin manager...")

        # 按加载顺序的逆序卸载插件
        for plugin_name in reversed(self.load_order):
            self.unload_plugin(plugin_name)

        self.plugins.clear()
        self.plugin_metadata.clear()
        self.load_order.clear()

        self.logger.info("Plugin manager shutdown completed")
