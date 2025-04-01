import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Literal


class VariableManager:
    """
    变量管理器，用于管理测试过程中的变量
    支持全局变量、测试用例级别变量和临时变量
    支持内存存储和文件存储两种模式
    """

    _instance = None

    def __new__(cls, storage_mode: str = "file", storage_file: str = None):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(VariableManager, cls).__new__(cls)
            cls._instance._initialize(storage_mode, storage_file)
        return cls._instance

    def _initialize(self, storage_mode: str = "memory", storage_file: str = None):
        """
        初始化变量存储
        
        Args:
            storage_mode: 存储模式，可选值：memory, file
            storage_file: 文件存储模式下的存储文件路径
        """
        self.logger = logging.getLogger(__name__)
        self.storage_mode = storage_mode

        # 内存存储模式的变量
        self.variables = {
            "global": {},  # 全局变量，跨测试用例持久化
            "test_case": {},  # 测试用例级别变量，仅在当前测试用例内有效
            "temp": {}  # 临时变量，用于特定操作内部使用
        }

        # 文件存储模式的配置
        if storage_file is None:
            storage_file = str(Path(__file__).parent.parent / "test_data" / "variables.json")
        self.storage_file = storage_file

        # 如果是文件存储模式，则加载文件中的变量
        if self.storage_mode == "file":
            self._load_variables_from_file()

    def _load_variables_from_file(self):
        """从存储文件加载变量"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    file_variables = json.load(f)
                    # 确保文件中的变量结构符合预期
                    for scope in ["global", "test_case", "temp"]:
                        if scope in file_variables and isinstance(file_variables[scope], dict):
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
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(self.variables, f, ensure_ascii=False, indent=2)
                self.logger.debug(f"变量已保存到文件: {self.storage_file}")
            except Exception as e:
                self.logger.error(f"保存变量到文件失败: {str(e)}")

    def set_storage_mode(self, mode: Literal["memory", "file"], storage_file: str = None):
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
            scope: 变量作用域，可选值：global, test_case, temp
        """
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

        # 如果是文件存储模式，保存到文件
        if self.storage_mode == "file":
            self._save_variables_to_file()

        self.logger.debug(f"设置变量 '{name}' = '{value}' (作用域: {scope}, 原值: {old_value})")

    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        获取变量值，优先级：test_case > global > temp
        
        Args:
            name: 变量名
            default: 如果变量不存在，返回的默认值
            
        Returns:
            变量值，如果不存在则返回默认值
        """
        # 按照优先级查找变量
        for scope in ["test_case", "global", "temp"]:
            if name in self.variables[scope]:
                return self.variables[scope][name]

        # 未找到变量，返回默认值
        self.logger.debug(f"未找到变量 '{name}'，返回默认值: {default}")
        return default

    def get_variable_from_scope(self, name: str, scope: str = "global", default: Any = None) -> Any:
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

    def import_variables(self, variables: Dict[str, Any], scope: str = "global", overwrite: bool = True):
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
