import json
import os
from pathlib import Path
from typing import Any, Dict


class VariableManager:
    """变量管理器，用于存储和管理测试用例间的变量"""

    def __init__(self, storage_file: str = None):
        """
        初始化变量管理器
        Args:
            storage_file: 变量存储文件路径，如果不指定则使用默认路径
        """
        if storage_file is None:
            storage_file = str(Path(__file__).parent.parent / "test_data" / "variables.json")
        self.storage_file = storage_file
        self._variables: Dict[str, Any] = {}
        self._load_variables()

    def _load_variables(self):
        """从存储文件加载变量"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self._variables = json.load(f)
            except json.JSONDecodeError:
                self._variables = {}
        else:
            # 确保存储目录存在
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            self._variables = {}

    def _save_variables(self):
        """保存变量到存储文件"""
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self._variables, f, ensure_ascii=False, indent=2)

    def set_variable(self, name: str, value: Any, scope: str = "global"):
        """
        设置变量
        Args:
            name: 变量名
            value: 变量值
            scope: 变量作用域，可以是 "global" 或特定的测试用例名
        """
        if scope not in self._variables:
            self._variables[scope] = {}
        self._variables[scope][name] = value
        self._save_variables()

    def get_variable(self, name: str, scope: str = "global", default: Any = None) -> Any:
        """
        获取变量值
        Args:
            name: 变量名
            scope: 变量作用域
            default: 默认值，当变量不存在时返回
        Returns:
            变量值
        """
        scope_vars = self._variables.get(scope, {})
        return scope_vars.get(name, default)

    def clear_scope(self, scope: str):
        """
        清除指定作用域的所有变量
        Args:
            scope: 要清除的作用域
        """
        if scope in self._variables:
            del self._variables[scope]
            self._save_variables()

    def clear_all(self):
        """清除所有变量"""
        self._variables.clear()
        self._save_variables()

    def list_variables(self, scope: str = None) -> Dict[str, Any]:
        """
        列出变量
        Args:
            scope: 指定作用域，如果为None则列出所有作用域的变量
        Returns:
            变量字典
        """
        if scope:
            return self._variables.get(scope, {})
        return self._variables
