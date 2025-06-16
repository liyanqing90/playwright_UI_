"""变量管理服务

提供变量存储、替换和管理功能。
"""

import re
import time
from typing import Protocol, Dict, Any

from utils.logger import logger
from .base_service import BaseService


class VariableOperations(Protocol):
    """变量操作协议"""
    
    def set_variable(self, name: str, value: Any) -> None:
        """设置变量"""
        ...
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量"""
        ...
    
    def replace_variables_refactored(self, value: Any, scope: str = None) -> Any:
        """替换值中的变量引用（兼容VariableManager接口）
        
        Args:
            value: 要处理的值
            scope: 变量作用域（忽略，为了兼容）
            
        Returns:
            Any: 处理后的值
        """
        if isinstance(value, str):
            return self.replace_variables(value)
        return value
    
    def replace_variables(self, text: str) -> str:
        """替换文本中的变量"""
        ...
    
    def clear_variables(self) -> None:
        """清空所有变量"""
        ...
    
    def get_all_variables(self) -> Dict[str, Any]:
        """获取所有变量"""
        ...

class VariableService(BaseService):
    """变量管理服务实现"""
    
    def __init__(self, performance_manager=None):
        super().__init__(performance_manager)
        self._variables: Dict[str, Any] = {}
        self._variable_pattern = re.compile(r'\$\{([^}]+)\}')
    
    def set_variable(self, name: str, value: Any, scope: str = "test_case") -> None:
        """设置变量
        
        Args:
            name: 变量名
            value: 变量值
            scope: 变量作用域（为了兼容VariableManager接口）
        """
        start_time = time.time()
        
        try:
            self._log_operation("set_variable", f"name: {name}, value: {value}")
            
            self._variables[name] = value
            
            duration = time.time() - start_time
            self._record_operation("set_variable", duration, True)
            
            logger.debug(f"变量设置成功: {name} = {value}")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("set_variable", duration, False)
            logger.error(f"设置变量失败: {name}, 错误: {e}")
            raise
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量
        
        Args:
            name: 变量名
            default: 默认值
            
        Returns:
            Any: 变量值
        """
        start_time = time.time()
        
        try:
            self._log_operation("get_variable", f"name: {name}")
            
            value = self._variables.get(name, default)
            
            duration = time.time() - start_time
            self._record_operation("get_variable", duration, True)
            
            logger.debug(f"获取变量: {name} = {value}")
            return value
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("get_variable", duration, False)
            logger.error(f"获取变量失败: {name}, 错误: {e}")
            raise
    
    def replace_variables(self, text: str) -> str:
        """替换文本中的变量
        
        支持的格式:
        - ${variable_name}: 替换为变量值
        - ${variable_name:default_value}: 如果变量不存在，使用默认值
        
        Args:
            text: 包含变量占位符的文本
            
        Returns:
            str: 替换后的文本
        """
        if not isinstance(text, str):
            return text
        
        start_time = time.time()
        
        try:
            self._log_operation("replace_variables", f"text: {text[:100]}...")
            
            def replace_match(match):
                var_expr = match.group(1)
                
                # 检查是否有默认值
                if ':' in var_expr:
                    var_name, default_value = var_expr.split(':', 1)
                    var_name = var_name.strip()
                    default_value = default_value.strip()
                else:
                    var_name = var_expr.strip()
                    default_value = match.group(0)  # 保持原样
                
                # 获取变量值
                if var_name in self._variables:
                    value = self._variables[var_name]
                    # 转换为字符串
                    return str(value) if value is not None else ''
                else:
                    return default_value
            
            result = self._variable_pattern.sub(replace_match, text)
            
            duration = time.time() - start_time
            self._record_operation("replace_variables", duration, True)
            
            if result != text:
                logger.debug(f"变量替换完成: '{text[:50]}...' -> '{result[:50]}...'")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("replace_variables", duration, False)
            logger.error(f"变量替换失败: {text[:50]}..., 错误: {e}")
            raise
    
    def clear_variables(self) -> None:
        """清空所有变量"""
        start_time = time.time()
        
        try:
            self._log_operation("clear_variables", "")
            
            count = len(self._variables)
            self._variables.clear()
            
            duration = time.time() - start_time
            self._record_operation("clear_variables", duration, True)
            
            logger.debug(f"清空变量完成: 清除了 {count} 个变量")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("clear_variables", duration, False)
            logger.error(f"清空变量失败: {e}")
            raise
    
    def get_all_variables(self) -> Dict[str, Any]:
        """获取所有变量
        
        Returns:
            Dict[str, Any]: 所有变量的副本
        """
        start_time = time.time()
        
        try:
            self._log_operation("get_all_variables", "")
            
            result = self._variables.copy()
            
            duration = time.time() - start_time
            self._record_operation("get_all_variables", duration, True)
            
            logger.debug(f"获取所有变量: {len(result)} 个变量")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("get_all_variables", duration, False)
            logger.error(f"获取所有变量失败: {e}")
            raise
    
    def delete_variable(self, name: str) -> bool:
        """删除变量
        
        Args:
            name: 变量名
            
        Returns:
            bool: 是否成功删除
        """
        start_time = time.time()
        
        try:
            self._log_operation("delete_variable", f"name: {name}")
            
            if name in self._variables:
                del self._variables[name]
                success = True
                logger.debug(f"删除变量成功: {name}")
            else:
                success = False
                logger.debug(f"变量不存在: {name}")
            
            duration = time.time() - start_time
            self._record_operation("delete_variable", duration, success)
            
            return success
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("delete_variable", duration, False)
            logger.error(f"删除变量失败: {name}, 错误: {e}")
            raise
    
    def has_variable(self, name: str) -> bool:
        """检查变量是否存在
        
        Args:
            name: 变量名
            
        Returns:
            bool: 变量是否存在
        """
        try:
            self._log_operation("has_variable", f"name: {name}")
            
            exists = name in self._variables
            
            logger.debug(f"检查变量存在: {name} = {exists}")
            return exists
            
        except Exception as e:
            logger.error(f"检查变量存在失败: {name}, 错误: {e}")
            raise
    
    def set_variables_from_dict(self, variables: Dict[str, Any]) -> None:
        """从字典批量设置变量
        
        Args:
            variables: 变量字典
        """
        start_time = time.time()
        
        try:
            self._log_operation("set_variables_from_dict", f"count: {len(variables)}")
            
            self._variables.update(variables)
            
            duration = time.time() - start_time
            self._record_operation("set_variables_from_dict", duration, True)
            
            logger.debug(f"批量设置变量完成: {len(variables)} 个变量")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("set_variables_from_dict", duration, False)
            logger.error(f"批量设置变量失败: {e}")
            raise
    
    def get_variable_names(self) -> list[str]:
        """获取所有变量名
        
        Returns:
            list[str]: 变量名列表
        """
        try:
            self._log_operation("get_variable_names", "")
            
            names = list(self._variables.keys())
            
            logger.debug(f"获取变量名列表: {len(names)} 个变量")
            return names
            
        except Exception as e:
            logger.error(f"获取变量名列表失败: {e}")
            raise
    
    def export_variables(self) -> str:
        """导出变量为JSON字符串
        
        Returns:
            str: JSON格式的变量数据
        """
        start_time = time.time()
        
        try:
            import json
            
            self._log_operation("export_variables", "")
            
            # 处理不能序列化的值
            exportable_vars = {}
            for name, value in self._variables.items():
                try:
                    json.dumps(value)  # 测试是否可序列化
                    exportable_vars[name] = value
                except (TypeError, ValueError):
                    exportable_vars[name] = str(value)  # 转换为字符串
            
            result = json.dumps(exportable_vars, ensure_ascii=False, indent=2)
            
            duration = time.time() - start_time
            self._record_operation("export_variables", duration, True)
            
            logger.debug(f"导出变量完成: {len(exportable_vars)} 个变量")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("export_variables", duration, False)
            logger.error(f"导出变量失败: {e}")
            raise
    
    def import_variables(self, json_data: str) -> None:
        """从JSON字符串导入变量
        
        Args:
            json_data: JSON格式的变量数据
        """
        start_time = time.time()
        
        try:
            import json
            
            self._log_operation("import_variables", f"data length: {len(json_data)}")
            
            variables = json.loads(json_data)
            
            if not isinstance(variables, dict):
                raise ValueError("JSON数据必须是对象格式")
            
            self._variables.update(variables)
            
            duration = time.time() - start_time
            self._record_operation("import_variables", duration, True)
            
            logger.debug(f"导入变量完成: {len(variables)} 个变量")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation("import_variables", duration, False)
            logger.error(f"导入变量失败: {e}")
            raise