import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Literal

from loguru import logger

from src.utils import singleton


@singleton
class VariableManager:
    """
    变量管理器，用于管理测试过程中的变量
    支持全局变量、测试用例级别变量和临时变量
    支持内存存储和文件存储两种模式

    使用装饰器实现单例模式，更加简洁和易于理解
    """

    def __init__(self, storage_mode: str = "memory", storage_file: str = None):
        """
        初始化变量管理器

        Args:
            storage_mode: 存储模式，可选值：memory, file
            storage_file: 文件存储模式下的存储文件路径
        """
        self.logger = logger
        self.storage_mode = storage_mode

        # 内存存储模式的变量
        self.variables = {
            "global": {},  # 全局变量，跨测试用例持久化
            "test_case": {},  # 测试用例级别变量，仅在当前测试用例内有效
            "module": {},  # 模块级别变量，仅在当前模块内有效
            "step": {},  # 步骤级别变量，仅在当前步骤内有效
            "temp": {},  # 临时变量，用于特定操作内部使用
        }

        # 变量作用域继承关系
        self.scope_hierarchy = {
            "step": ["step", "module", "test_case", "global"],
            "module": ["module", "test_case", "global"],
            "test_case": ["test_case", "global"],
            "global": ["global"],
            "temp": ["temp", "step", "module", "test_case", "global"],
        }

        # 变量缓存 - 使用LRU缓存机制
        self._variable_cache = {}
        self._cache_access_order = []  # 记录访问顺序，用于LRU
        self._max_cache_size = 1000  # 最大缓存大小

        # 变量替换结果缓存
        self._replacement_cache = {}
        self._replacement_cache_order = []
        self._max_replacement_cache_size = 500

        # 变量访问统计
        self._stats = {
            "get_count": 0,
            "set_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "replacement_cache_hits": 0,
            "replacement_cache_misses": 0,
        }

        # 文件存储模式的配置
        if storage_file is None:
            storage_file = str(
                Path(__file__).parent.parent / "test_data" / "variables.json"
            )
        self.storage_file = storage_file

        # 如果是文件存储模式，则加载文件中的变量
        if self.storage_mode == "file":
            self._load_variables_from_file()

    def _load_variables_from_file(self):
        """从存储文件加载变量"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    file_variables = json.load(f)
                    # 确保文件中的变量结构符合预期
                    for scope in ["global", "test_case", "temp"]:
                        if scope in file_variables and isinstance(
                            file_variables[scope], dict
                        ):
                            self.variables[scope] = file_variables[scope]
                        else:
                            self.variables[scope] = {}
            except json.JSONDecodeError:
                self.logger.error(f"无法解析变量存储文件: {self.storage_file}")
                # 初始化为空字典
                for scope in ["global", "test_case", "temp"]:
                    self.variables[scope] = {}
        else:
            # 确保存储目录存在
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            # 初始化为空字典
            for scope in ["global", "test_case", "temp"]:
                self.variables[scope] = {}

    def _save_variables_to_file(self):
        """保存变量到存储文件"""
        if self.storage_mode == "file":
            try:
                with open(self.storage_file, "w", encoding="utf-8") as f:
                    json.dump(self.variables, f, ensure_ascii=False, indent=2)
                self.logger.debug(f"变量已保存到文件: {self.storage_file}")
            except Exception as e:
                self.logger.error(f"保存变量到文件失败: {str(e)}")

    def set_storage_mode(
        self, mode: Literal["memory", "file"], storage_file: str = None
    ):
        """
        设置存储模式

        Args:
            mode: 存储模式，可选值：memory, file
            storage_file: 文件存储模式下的存储文件路径
        """
        if mode not in ["memory", "file"]:
            self.logger.warning(f"无效的存储模式: {mode}，将使用默认模式 memory")
            mode = "memory"

        old_mode = self.storage_mode
        self.storage_mode = mode

        if mode == "file":
            if storage_file is not None:
                self.storage_file = storage_file

            # 如果从内存模式切换到文件模式，保存当前内存中的变量到文件
            if old_mode == "memory":
                self._save_variables_to_file()
            else:
                # 重新加载文件中的变量
                self._load_variables_from_file()

        self.logger.info(f"存储模式已切换: {old_mode} -> {mode}")

    def reset(self):
        """重置所有变量"""
        for scope in self.variables:
            self.variables[scope] = {}

        if self.storage_mode == "file":
            self._save_variables_to_file()

        self.logger.debug("所有变量已重置")

    def clear_scope(self, scope: str = "test_case"):
        """
        清除指定作用域的所有变量

        Args:
            scope: 变量作用域，默认为test_case
        """
        if scope in self.variables:
            self.variables[scope] = {}

            if self.storage_mode == "file":
                self._save_variables_to_file()

            self.logger.debug(f"已清除 {scope} 作用域的所有变量")
        else:
            self.logger.warning(f"无效的作用域: {scope}")

    def set_variable(self, name: str, value: Any, scope: str = "test_case"):
        """
        设置变量

        Args:
            name: 变量名
            value: 变量值
            scope: 变量作用域，可选值：global, test_case, module, step, temp
        """
        # 增加访问计数
        self._stats["set_count"] += 1

        if scope not in self.variables:
            self.logger.warning(f"无效的作用域: {scope}，将使用默认作用域 test_case")
            scope = "test_case"

        # 处理变量名，确保合法
        name = str(name).strip()
        if not name:
            self.logger.error("变量名不能为空")
            return

        # 设置变量值
        old_value = self.variables[scope].get(name, "未定义")
        self.variables[scope][name] = value

        # 清除相关缓存
        self._clear_variable_cache(name)

        # 如果是文件存储模式，保存到文件
        if self.storage_mode == "file":
            self._save_variables_to_file()

        self.logger.debug(
            f"设置变量 '{name}' = '{value}' (作用域: {scope}, 原值: {old_value})"
        )

    def _clear_variable_cache(self, name: str = None):
        """
        清除变量缓存

        Args:
            name: 变量名，如果为 None，则清除所有缓存
        """
        if name is None:
            # 清除所有缓存
            self._variable_cache.clear()
            self._cache_access_order.clear()
            self._replacement_cache.clear()
            self._replacement_cache_order.clear()
            return

        # 清除指定变量的缓存
        keys_to_remove = []
        for cache_key in self._variable_cache:
            if cache_key.startswith(f"{name}:"):
                keys_to_remove.append(cache_key)

        for key in keys_to_remove:
            del self._variable_cache[key]
            if key in self._cache_access_order:
                self._cache_access_order.remove(key)

        # 清除替换缓存中相关的条目
        replacement_keys_to_remove = []
        for cache_key in self._replacement_cache:
            if name in cache_key:  # 简单的包含检查
                replacement_keys_to_remove.append(cache_key)

        for key in replacement_keys_to_remove:
            del self._replacement_cache[key]
            if key in self._replacement_cache_order:
                self._replacement_cache_order.remove(key)

    def _manage_cache_size(self):
        """管理缓存大小，实现LRU策略"""
        # 管理变量缓存
        while len(self._variable_cache) > self._max_cache_size:
            if self._cache_access_order:
                oldest_key = self._cache_access_order.pop(0)
                if oldest_key in self._variable_cache:
                    del self._variable_cache[oldest_key]

        # 管理替换缓存
        while len(self._replacement_cache) > self._max_replacement_cache_size:
            if self._replacement_cache_order:
                oldest_key = self._replacement_cache_order.pop(0)
                if oldest_key in self._replacement_cache:
                    del self._replacement_cache[oldest_key]

    def _update_cache_access(self, cache_key: str, is_replacement_cache: bool = False):
        """更新缓存访问顺序"""
        if is_replacement_cache:
            if cache_key in self._replacement_cache_order:
                self._replacement_cache_order.remove(cache_key)
            self._replacement_cache_order.append(cache_key)
        else:
            if cache_key in self._cache_access_order:
                self._cache_access_order.remove(cache_key)
            self._cache_access_order.append(cache_key)

    def get_variable(
        self, name: str, scope: Optional[str] = None, default: Any = None
    ) -> Any:
        """
        获取变量值，支持作用域继承

        Args:
            name: 变量名
            scope: 变量作用域，如果为 None，则按照默认优先级查找
            default: 如果变量不存在，返回的默认值

        Returns:
            变量值，如果不存在则返回默认值
        """
        # 增加访问计数
        self._stats["get_count"] += 1

        # 检查缓存
        cache_key = f"{name}:{scope if scope else 'default'}"
        if cache_key in self._variable_cache:
            self._stats["cache_hits"] += 1
            self._update_cache_access(cache_key)
            return self._variable_cache[cache_key]

        self._stats["cache_misses"] += 1

        # 如果指定了作用域，则按照作用域继承关系查找
        if scope in self.scope_hierarchy:
            for search_scope in self.scope_hierarchy[scope]:
                if name in self.variables[search_scope]:
                    value = self.variables[search_scope][name]
                    # 将结果存入缓存
                    self._variable_cache[cache_key] = value
                    self._update_cache_access(cache_key)
                    self._manage_cache_size()
                    return value
        else:
            # 没有指定作用域，按照默认优先级查找
            for search_scope in ["test_case", "module", "global", "step", "temp"]:
                if name in self.variables[search_scope]:
                    value = self.variables[search_scope][name]
                    # 将结果存入缓存
                    self._variable_cache[cache_key] = value
                    self._update_cache_access(cache_key)
                    self._manage_cache_size()
                    return value

        # 未找到变量，返回默认值
        self.logger.debug(f"未找到变量 '{name}'，返回默认值: {default}")
        # 将默认值存入缓存
        self._variable_cache[cache_key] = default
        return default

    def get_variable_from_scope(
        self, name: str, scope: str = "global", default: Any = None
    ) -> Any:
        """
        从指定作用域获取变量值

        Args:
            name: 变量名
            scope: 变量作用域
            default: 如果变量不存在，返回的默认值

        Returns:
            变量值，如果不存在则返回默认值
        """
        if scope not in self.variables:
            self.logger.warning(f"无效的作用域: {scope}")
            return default

        return self.variables[scope].get(name, default)

    def remove_variable(self, name: str, scope: Optional[str] = None) -> bool:
        """
        删除变量

        Args:
            name: 变量名
            scope: 变量作用域，如果为None则尝试从所有作用域中删除

        Returns:
            是否成功删除至少一个变量
        """
        removed = False

        if scope is not None:
            # 从指定作用域删除
            if scope in self.variables and name in self.variables[scope]:
                del self.variables[scope][name]
                removed = True
                self.logger.debug(f"已删除变量 '{name}' (作用域: {scope})")
        else:
            # 从所有作用域删除
            for scope_name in self.variables:
                if name in self.variables[scope_name]:
                    del self.variables[scope_name][name]
                    removed = True
                    self.logger.debug(f"已删除变量 '{name}' (作用域: {scope_name})")

        # 如果是文件存储模式且有变量被删除，保存到文件
        if removed and self.storage_mode == "file":
            self._save_variables_to_file()

        if not removed:
            self.logger.debug(f"未找到要删除的变量 '{name}'")

        return removed

    def list_variables(self, scope: Optional[str] = None) -> Dict[str, Any]:
        """
        列出变量

        Args:
            scope: 变量作用域，如果为None则列出所有作用域的变量

        Returns:
            变量字典
        """
        if scope is not None:
            if scope in self.variables:
                return self.variables[scope].copy()
            else:
                self.logger.warning(f"无效的作用域: {scope}")
                return {}
        else:
            # 合并所有作用域的变量，按优先级覆盖
            result = {}
            # 按照global -> test_case -> temp的顺序合并，保持最高优先级
            for scope_name in ["global", "test_case", "temp"]:
                result.update(self.variables[scope_name])
            return result

    def export_variables(self, scope: Optional[str] = None) -> Dict[str, Any]:
        """
        导出变量，用于持久化或共享

        Args:
            scope: 变量作用域，如果为None则导出所有作用域的变量

        Returns:
            变量字典
        """
        return self.list_variables(scope)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取变量管理器的统计信息

        Returns:
            统计信息字典
        """
        # 计算缓存命中率
        hit_rate = 0
        if self._stats["get_count"] > 0:
            hit_rate = self._stats["cache_hits"] / self._stats["get_count"] * 100

        # 添加缓存大小和命中率
        stats = {
            **self._stats,
            "cache_size": len(self._variable_cache),
            "cache_hit_rate": f"{hit_rate:.2f}%",
            "scopes": {scope: len(vars) for scope, vars in self.variables.items()},
        }

        return stats

    def reset_stats(self):
        """重置统计信息"""
        self._stats = {
            "get_count": 0,
            "set_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    def debug_info(self) -> str:
        """
        获取变量管理器的调试信息

        Returns:
            调试信息字符串
        """
        stats = self.get_stats()

        info = [
            "=== 变量管理器调试信息 ===",
            f"存储模式: {self.storage_mode}",
            f"变量访问次数: 获取={stats['get_count']}, 设置={stats['set_count']}",
            f"缓存命中率: {stats['cache_hit_rate']} ({stats['cache_hits']}/{stats['get_count']})",
            f"缓存大小: {stats['cache_size']} 项",
            "变量数量:",
        ]

        for scope, count in stats["scopes"].items():
            info.append(f"  - {scope}: {count} 个变量")

        return "\n".join(info)

    def import_variables(
        self, variables: Dict[str, Any], scope: str = "global", overwrite: bool = True
    ):
        """
        导入变量

        Args:
            variables: 要导入的变量字典
            scope: 导入到的作用域
            overwrite: 是否覆盖已存在的变量
        """
        if scope not in self.variables:
            self.logger.warning(f"无效的作用域: {scope}，将使用默认作用域 global")
            scope = "global"

        changes_made = False
        for name, value in variables.items():
            if not overwrite and name in self.variables[scope]:
                self.logger.debug(f"跳过已存在的变量 '{name}' (作用域: {scope})")
                continue

            self.variables[scope][name] = value
            changes_made = True
            self.logger.debug(f"导入变量 '{name}' = '{value}' (作用域: {scope})")

        # 如果是文件存储模式且有变量被导入，保存到文件
        if changes_made and self.storage_mode == "file":
            self._save_variables_to_file()

    def replace_variables_refactored(
        self, value: Any, scope: Optional[str] = None
    ) -> Any:
        """
        替换值中的变量引用。递归处理字符串、列表、字典。
        对整个值是变量引用的字符串保留原始类型。

        Args:
            value: 要处理的值，可能包含变量引用
            scope: 变量作用域，如果为 None，则按照优先级查找变量

        Returns:
            处理后的值
        """
        # 直接返回 None, 数字, 布尔等非容器类型
        if value is None or not isinstance(value, (str, list, dict)):
            return value

        # 处理字符串
        if isinstance(value, str):
            # 优化：如果字符串中没有 $ 符号，直接返回
            if "$" not in value:
                return value

            # 检查替换缓存
            replacement_cache_key = f"{value}:{scope if scope else 'default'}"
            if replacement_cache_key in self._replacement_cache:
                self._stats["replacement_cache_hits"] += 1
                self._update_cache_access(replacement_cache_key, is_replacement_cache=True)
                return self._replacement_cache[replacement_cache_key]

            self._stats["replacement_cache_misses"] += 1

            # 检查整个字符串是否就是一个变量引用，以保留原始类型
            # 支持两种格式：${var_name} 和 $<var_name>
            exact_match_pattern = r"^\${([^}]+)}$|^\$<([^>]+)>$"
            exact_match = re.fullmatch(exact_match_pattern, value)

            if exact_match:
                # 获取变量名，可能在第一个或第二个捕获组中
                var_name = (
                    exact_match.group(1)
                    if exact_match.group(1) is not None
                    else exact_match.group(2)
                )
                # 精确匹配，直接获取并返回原始类型的值
                result = self.get_variable(var_name)

                # 将结果存入替换缓存
                self._replacement_cache[replacement_cache_key] = result
                self._update_cache_access(replacement_cache_key, is_replacement_cache=True)
                self._manage_cache_size()

                return result

            # 优化：使用缓存存储编译后的正则表达式
            if not hasattr(self, "_compiled_patterns"):
                self._compiled_patterns = {
                    "embedded_var": re.compile(r"\$\{([^}]+)\}|\$<([^>]+)>"),
                }

            # 定义变量替换函数
            def _variable_replacer(match):
                # 获取变量名，可能在第一个或第二个捕获组中
                var_name = (
                    match.group(1) if match.group(1) is not None else match.group(2)
                )

                # 获取变量值
                var_value = self.get_variable(var_name)

                if var_value is None:
                    # 变量未定义，警告并保留原始引用
                    logger.debug(f"变量 '{var_name}' 未定义，保留原始引用")
                    return match.group(0)  # 返回原始引用
                else:
                    # 变量找到，转换为字符串进行替换
                    return str(var_value)

            # 使用编译后的正则表达式替换所有内嵌变量
            result = self._compiled_patterns["embedded_var"].sub(
                _variable_replacer, value
            )

            # 将结果存入替换缓存
            self._replacement_cache[replacement_cache_key] = result
            self._update_cache_access(replacement_cache_key, is_replacement_cache=True)
            self._manage_cache_size()

            return result

        # 处理列表 (递归)
        if isinstance(value, list):
            # 优化：使用列表推导式而不是循环
            return [self.replace_variables_refactored(item, scope) for item in value]

        # 处理字典 (递归)
        if isinstance(value, dict):
            # 优化：使用字典推导式
            return {
                k: self.replace_variables_refactored(v, scope) for k, v in value.items()
            }

        return value  # 改为返回原始值而不是 None
