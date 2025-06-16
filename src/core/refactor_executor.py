"""重构执行器

实际执行分层架构与插件系统职责划分的重构操作。
"""

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from utils.logger import logger


@dataclass
class RefactorOperation:
    """重构操作"""
    operation_type: str  # move, remove, create, modify
    source_path: str
    target_path: Optional[str] = None
    description: str = ""
    backup_required: bool = True

class RefactorExecutor:
    """重构执行器
    
    负责执行具体的重构操作，包括文件移动、删除、修改等。
    """
    
    def __init__(self, project_root: str = "/Users/mac/PycharmProjects/zhijia_ui"):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "backup" / "refactor_backup"
        self.operations_log = []
    
    def execute_phase1_core_boundary_cleanup(self):
        """执行第一阶段：核心边界清理"""
        logger.info("开始执行第一阶段：核心边界清理")
        
        operations = [
            # 清理核心服务中的非必需功能
            RefactorOperation(
                operation_type="modify",
                source_path="src/core/services/assertion_service.py",
                description="移除高级断言功能，保留基础断言"
            ),
            
            # 确保核心服务实现标准接口
            RefactorOperation(
                operation_type="modify",
                source_path="src/core/services/element_service.py",
                description="确保实现ServiceInterface"
            ),
            
            RefactorOperation(
                operation_type="modify",
                source_path="src/core/services/navigation_service.py",
                description="确保实现ServiceInterface"
            ),
            
            RefactorOperation(
                operation_type="modify",
                source_path="src/core/services/wait_service.py",
                description="确保实现ServiceInterface"
            )
        ]
        
        for operation in operations:
            self._execute_operation(operation)
    
    def execute_phase2_eliminate_duplicates(self):
        """执行第二阶段：消除重复功能"""
        logger.info("开始执行第二阶段：消除重复功能")
        
        # 断言功能重构
        self._refactor_assertion_duplicates()
        
        # 性能监控重构
        self._refactor_performance_duplicates()
    
    def _refactor_assertion_duplicates(self):
        """重构断言功能重复"""
        logger.info("重构断言功能重复")
        
        # 定义核心断言功能（保留在核心服务中）
        core_assertions = [
            'assert_element_visible',
            'assert_element_not_visible',
            'assert_text_equals',
            'assert_text_contains',
            'assert_url_equals',
            'assert_url_contains',
            'assert_attribute_equals',
            'assert_element_enabled',
            'assert_element_disabled'
        ]
        
        # 定义高级断言功能（移动到插件中）
        advanced_assertions = [
            'soft_assert',
            'batch_assert',
            'retry_assert',
            'timeout_assert',
            'json_schema_assert',
            'custom_matcher_assert'
        ]
        
        # 创建核心断言服务的清理版本
        core_assertion_content = self._generate_core_assertion_service(core_assertions)
        
        operation = RefactorOperation(
            operation_type="modify",
            source_path="src/core/services/assertion_service.py",
            description="清理核心断言服务，只保留基础断言功能"
        )
        
        self._execute_operation(operation, content=core_assertion_content)
        
        # 更新插件断言功能，移除与核心重复的部分
        plugin_assertion_content = self._generate_plugin_assertion_service(advanced_assertions)
        
        operation = RefactorOperation(
            operation_type="modify",
            source_path="plugins/assertion_commands/plugin.py",
            description="更新插件断言功能，专注于高级断言"
        )
        
        self._execute_operation(operation, content=plugin_assertion_content)
    
    def _refactor_performance_duplicates(self):
        """重构性能监控重复"""
        logger.info("重构性能监控重复")
        
        # 核心服务只保留基础性能记录接口
        base_service_content = self._generate_base_service_performance()
        
        operation = RefactorOperation(
            operation_type="modify",
            source_path="src/core/services/base_service.py",
            description="简化基础服务性能记录，提供标准接口"
        )
        
        self._execute_operation(operation, content=base_service_content)
    
    def _generate_core_assertion_service(self, core_assertions: List[str]) -> str:
        """生成核心断言服务内容"""
        return '''"""核心断言服务

提供基础、稳定的断言功能。
高级断言功能请使用assertion_commands插件。
"""

from typing import Optional, Any
from playwright.sync_api import Page, Locator
from src.core.services.base_service import BaseService
from src.core.interfaces.service_interface import ServiceInterface, ConfigurableService
from utils.logger import logger

class AssertionOperations:
    """基础断言操作接口"""
    
    def assert_element_visible(self, selector: str, timeout: int = 5000) -> bool:
        """断言元素可见"""
        pass
    
    def assert_element_not_visible(self, selector: str, timeout: int = 5000) -> bool:
        """断言元素不可见"""
        pass
    
    def assert_text_equals(self, selector: str, expected_text: str, timeout: int = 5000) -> bool:
        """断言文本相等"""
        pass
    
    def assert_text_contains(self, selector: str, expected_text: str, timeout: int = 5000) -> bool:
        """断言文本包含"""
        pass
    
    def assert_url_equals(self, expected_url: str) -> bool:
        """断言URL相等"""
        pass
    
    def assert_url_contains(self, expected_text: str) -> bool:
        """断言URL包含"""
        pass
    
    def assert_attribute_equals(self, selector: str, attribute: str, expected_value: str, timeout: int = 5000) -> bool:
        """断言属性值相等"""
        pass
    
    def assert_element_enabled(self, selector: str, timeout: int = 5000) -> bool:
        """断言元素启用"""
        pass
    
    def assert_element_disabled(self, selector: str, timeout: int = 5000) -> bool:
        """断言元素禁用"""
        pass

class AssertionService(BaseService, AssertionOperations):
    """核心断言服务
    
    提供基础、稳定的断言功能。
    专注于最常用的断言操作，保证高性能和稳定性。
    
    高级断言功能（软断言、批量断言、重试断言等）
    请使用assertion_commands插件。
    """
    
    def __init__(self, page: Page, performance_manager=None, variable_manager=None):
        super().__init__(performance_manager)
        self.page = page
        self.variable_manager = variable_manager
    
    def get_service_name(self) -> str:
        return "assertion_service"
    
    def _do_initialize(self) -> bool:
        """初始化断言服务"""
        try:
            # 验证page对象
            if not self.page:
                logger.error("Page对象未提供")
                return False
            
            logger.info("断言服务初始化成功")
            return True
        except Exception as e:
            logger.error(f"断言服务初始化失败: {e}")
            return False
    
    def _do_cleanup(self):
        """清理断言服务"""
        logger.info("断言服务清理完成")
    
    def assert_element_visible(self, selector: str, timeout: int = 5000) -> bool:
        """断言元素可见"""
        operation_name = "assert_element_visible"
        self._log_operation(operation_name, {"selector": selector, "timeout": timeout})
        
        try:
            locator = self._get_locator(selector)
            locator.wait_for(state="visible", timeout=timeout)
            
            self._record_operation(operation_name, True)
            logger.info(f"断言成功：元素 {selector} 可见")
            return True
            
        except Exception as e:
            self._record_operation(operation_name, False)
            logger.error(f"断言失败：元素 {selector} 不可见 - {e}")
            raise AssertionError(f"元素 {selector} 不可见: {e}")
    
    def assert_element_not_visible(self, selector: str, timeout: int = 5000) -> bool:
        """断言元素不可见"""
        operation_name = "assert_element_not_visible"
        self._log_operation(operation_name, {"selector": selector, "timeout": timeout})
        
        try:
            locator = self._get_locator(selector)
            locator.wait_for(state="hidden", timeout=timeout)
            
            self._record_operation(operation_name, True)
            logger.info(f"断言成功：元素 {selector} 不可见")
            return True
            
        except Exception as e:
            self._record_operation(operation_name, False)
            logger.error(f"断言失败：元素 {selector} 可见 - {e}")
            raise AssertionError(f"元素 {selector} 仍然可见: {e}")
    
    def assert_text_equals(self, selector: str, expected_text: str, timeout: int = 5000) -> bool:
        """断言文本相等"""
        operation_name = "assert_text_equals"
        self._log_operation(operation_name, {"selector": selector, "expected_text": expected_text, "timeout": timeout})
        
        try:
            # 变量替换
            if self.variable_manager:
                expected_text = self.variable_manager.replace_variables(expected_text)
            
            locator = self._get_locator(selector)
            actual_text = locator.text_content(timeout=timeout)
            
            if actual_text == expected_text:
                self._record_operation(operation_name, True)
                logger.info(f"断言成功：文本相等 - {actual_text}")
                return True
            else:
                self._record_operation(operation_name, False)
                error_msg = f"文本不相等 - 期望: {expected_text}, 实际: {actual_text}"
                logger.error(f"断言失败：{error_msg}")
                raise AssertionError(error_msg)
                
        except Exception as e:
            self._record_operation(operation_name, False)
            logger.error(f"断言失败：获取文本失败 - {e}")
            raise AssertionError(f"获取元素 {selector} 文本失败: {e}")
    
    def assert_text_contains(self, selector: str, expected_text: str, timeout: int = 5000) -> bool:
        """断言文本包含"""
        operation_name = "assert_text_contains"
        self._log_operation(operation_name, {"selector": selector, "expected_text": expected_text, "timeout": timeout})
        
        try:
            # 变量替换
            if self.variable_manager:
                expected_text = self.variable_manager.replace_variables(expected_text)
            
            locator = self._get_locator(selector)
            actual_text = locator.text_content(timeout=timeout)
            
            if expected_text in actual_text:
                self._record_operation(operation_name, True)
                logger.info(f"断言成功：文本包含 - {actual_text} 包含 {expected_text}")
                return True
            else:
                self._record_operation(operation_name, False)
                error_msg = f"文本不包含 - 期望包含: {expected_text}, 实际: {actual_text}"
                logger.error(f"断言失败：{error_msg}")
                raise AssertionError(error_msg)
                
        except Exception as e:
            self._record_operation(operation_name, False)
            logger.error(f"断言失败：获取文本失败 - {e}")
            raise AssertionError(f"获取元素 {selector} 文本失败: {e}")
    
    def assert_url_equals(self, expected_url: str) -> bool:
        """断言URL相等"""
        operation_name = "assert_url_equals"
        self._log_operation(operation_name, {"expected_url": expected_url})
        
        try:
            # 变量替换
            if self.variable_manager:
                expected_url = self.variable_manager.replace_variables(expected_url)
            
            actual_url = self.page.url
            
            if actual_url == expected_url:
                self._record_operation(operation_name, True)
                logger.info(f"断言成功：URL相等 - {actual_url}")
                return True
            else:
                self._record_operation(operation_name, False)
                error_msg = f"URL不相等 - 期望: {expected_url}, 实际: {actual_url}"
                logger.error(f"断言失败：{error_msg}")
                raise AssertionError(error_msg)
                
        except Exception as e:
            self._record_operation(operation_name, False)
            logger.error(f"断言失败：获取URL失败 - {e}")
            raise AssertionError(f"获取当前URL失败: {e}")
    
    def assert_url_contains(self, expected_text: str) -> bool:
        """断言URL包含"""
        operation_name = "assert_url_contains"
        self._log_operation(operation_name, {"expected_text": expected_text})
        
        try:
            # 变量替换
            if self.variable_manager:
                expected_text = self.variable_manager.replace_variables(expected_text)
            
            actual_url = self.page.url
            
            if expected_text in actual_url:
                self._record_operation(operation_name, True)
                logger.info(f"断言成功：URL包含 - {actual_url} 包含 {expected_text}")
                return True
            else:
                self._record_operation(operation_name, False)
                error_msg = f"URL不包含 - 期望包含: {expected_text}, 实际: {actual_url}"
                logger.error(f"断言失败：{error_msg}")
                raise AssertionError(error_msg)
                
        except Exception as e:
            self._record_operation(operation_name, False)
            logger.error(f"断言失败：获取URL失败 - {e}")
            raise AssertionError(f"获取当前URL失败: {e}")
    
    def assert_attribute_equals(self, selector: str, attribute: str, expected_value: str, timeout: int = 5000) -> bool:
        """断言属性值相等"""
        operation_name = "assert_attribute_equals"
        self._log_operation(operation_name, {
            "selector": selector, 
            "attribute": attribute, 
            "expected_value": expected_value, 
            "timeout": timeout
        })
        
        try:
            # 变量替换
            if self.variable_manager:
                expected_value = self.variable_manager.replace_variables(expected_value)
            
            locator = self._get_locator(selector)
            actual_value = locator.get_attribute(attribute, timeout=timeout)
            
            if actual_value == expected_value:
                self._record_operation(operation_name, True)
                logger.info(f"断言成功：属性值相等 - {attribute}={actual_value}")
                return True
            else:
                self._record_operation(operation_name, False)
                error_msg = f"属性值不相等 - 期望: {expected_value}, 实际: {actual_value}"
                logger.error(f"断言失败：{error_msg}")
                raise AssertionError(error_msg)
                
        except Exception as e:
            self._record_operation(operation_name, False)
            logger.error(f"断言失败：获取属性失败 - {e}")
            raise AssertionError(f"获取元素 {selector} 属性 {attribute} 失败: {e}")
    
    def assert_element_enabled(self, selector: str, timeout: int = 5000) -> bool:
        """断言元素启用"""
        operation_name = "assert_element_enabled"
        self._log_operation(operation_name, {"selector": selector, "timeout": timeout})
        
        try:
            locator = self._get_locator(selector)
            is_enabled = locator.is_enabled(timeout=timeout)
            
            if is_enabled:
                self._record_operation(operation_name, True)
                logger.info(f"断言成功：元素 {selector} 已启用")
                return True
            else:
                self._record_operation(operation_name, False)
                error_msg = f"元素 {selector} 未启用"
                logger.error(f"断言失败：{error_msg}")
                raise AssertionError(error_msg)
                
        except Exception as e:
            self._record_operation(operation_name, False)
            logger.error(f"断言失败：检查元素状态失败 - {e}")
            raise AssertionError(f"检查元素 {selector} 启用状态失败: {e}")
    
    def assert_element_disabled(self, selector: str, timeout: int = 5000) -> bool:
        """断言元素禁用"""
        operation_name = "assert_element_disabled"
        self._log_operation(operation_name, {"selector": selector, "timeout": timeout})
        
        try:
            locator = self._get_locator(selector)
            is_enabled = locator.is_enabled(timeout=timeout)
            
            if not is_enabled:
                self._record_operation(operation_name, True)
                logger.info(f"断言成功：元素 {selector} 已禁用")
                return True
            else:
                self._record_operation(operation_name, False)
                error_msg = f"元素 {selector} 未禁用"
                logger.error(f"断言失败：{error_msg}")
                raise AssertionError(error_msg)
                
        except Exception as e:
            self._record_operation(operation_name, False)
            logger.error(f"断言失败：检查元素状态失败 - {e}")
            raise AssertionError(f"检查元素 {selector} 禁用状态失败: {e}")
'''
    
    def _generate_plugin_assertion_service(self, advanced_assertions: List[str]) -> str:
        """生成插件断言服务内容（部分更新）"""
        return '''# 在现有plugin.py文件中添加以下注释和重构说明

"""
高级断言插件

提供扩展的断言功能，包括：
- 软断言（soft assertions）
- 批量断言（batch assertions）  
- 重试断言（retry assertions）
- 超时断言（timeout assertions）
- JSON模式断言（json schema assertions）
- 自定义匹配器断言（custom matcher assertions）

基础断言功能请使用核心的AssertionService。
"""

# 移除与核心AssertionService重复的基础断言方法：
# - assert_element_visible
# - assert_text_equals  
# - assert_url_contains
# 等基础断言功能

# 专注于高级断言功能的实现
'''
    
    def _generate_base_service_performance(self) -> str:
        """生成基础服务性能记录内容（部分更新）"""
        return '''# 在base_service.py中简化性能记录功能

# 只保留基础的性能记录接口，具体的性能分析和管理功能移到插件中

def _record_operation(self, operation_name: str, success: bool, duration: float = None):
    """记录操作性能 - 基础版本
    
    提供标准的性能记录接口，具体的性能分析请使用performance_management插件。
    """
    if self.performance_manager:
        self.performance_manager.record_basic_operation(
            operation_name=operation_name,
            success=success,
            duration=duration
        )
'''
    
    def _execute_operation(self, operation: RefactorOperation, content: str = None):
        """执行重构操作"""
        try:
            # 创建备份
            if operation.backup_required:
                self._create_backup(operation.source_path)
            
            source_file = self.project_root / operation.source_path
            
            if operation.operation_type == "modify" and content:
                # 修改文件内容
                with open(source_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"已修改文件: {operation.source_path}")
            
            elif operation.operation_type == "move":
                # 移动文件
                target_file = self.project_root / operation.target_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source_file), str(target_file))
                logger.info(f"已移动文件: {operation.source_path} -> {operation.target_path}")
            
            elif operation.operation_type == "remove":
                # 删除文件
                if source_file.exists():
                    source_file.unlink()
                    logger.info(f"已删除文件: {operation.source_path}")
            
            elif operation.operation_type == "create":
                # 创建文件
                source_file.parent.mkdir(parents=True, exist_ok=True)
                if content:
                    with open(source_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                logger.info(f"已创建文件: {operation.source_path}")
            
            # 记录操作
            self.operations_log.append({
                'operation': operation,
                'status': 'success',
                'timestamp': logger.info.__name__  # 简化时间戳
            })
            
        except Exception as e:
            logger.error(f"执行重构操作失败: {operation.description} - {e}")
            self.operations_log.append({
                'operation': operation,
                'status': 'failed',
                'error': str(e)
            })
            raise
    
    def _create_backup(self, file_path: str):
        """创建文件备份"""
        source_file = self.project_root / file_path
        if source_file.exists():
            backup_file = self.backup_dir / file_path
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(source_file), str(backup_file))
            logger.info(f"已创建备份: {backup_file}")
    
    def execute_full_refactor(self):
        """执行完整重构"""
        logger.info("开始执行完整重构计划")
        
        try:
            # 创建备份目录
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 执行各阶段重构
            self.execute_phase1_core_boundary_cleanup()
            self.execute_phase2_eliminate_duplicates()
            
            logger.info("重构执行完成")
            self._print_operations_summary()
            
        except Exception as e:
            logger.error(f"重构执行失败: {e}")
            self._print_operations_summary()
            raise
    
    def _print_operations_summary(self):
        """打印操作摘要"""
        logger.info("=== 重构操作摘要 ===")
        
        success_count = sum(1 for op in self.operations_log if op['status'] == 'success')
        failed_count = sum(1 for op in self.operations_log if op['status'] == 'failed')
        
        logger.info(f"总操作数: {len(self.operations_log)}")
        logger.info(f"成功: {success_count}")
        logger.info(f"失败: {failed_count}")
        
        if failed_count > 0:
            logger.info("失败操作:")
            for op in self.operations_log:
                if op['status'] == 'failed':
                    logger.error(f"  - {op['operation'].description}: {op.get('error', '未知错误')}")

if __name__ == "__main__":
    executor = RefactorExecutor()
    executor.execute_full_refactor()