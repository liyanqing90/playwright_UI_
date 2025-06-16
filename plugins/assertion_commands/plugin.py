"""断言命令插件实现

提供增强的断言功能，包括软断言、硬断言、条件断言、批量断言等。
"""

import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Callable

from src.automation.action_types import StepAction
from src.automation.commands.base_command import Command, CommandFactory
from utils.logger import logger


class AssertionType(Enum):
    """断言类型枚举"""
    SOFT = "soft"  # 软断言，失败时记录但继续执行
    HARD = "hard"  # 硬断言，失败时立即停止
    CONDITIONAL = "conditional"  # 条件断言，基于条件执行
    BATCH = "batch"  # 批量断言
    RETRY = "retry"  # 重试断言
    TIMEOUT = "timeout"  # 超时断言


class AssertionOperator(Enum):
    """断言操作符枚举"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    MATCHES = "matches"  # 正则匹配
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    IN = "in"
    NOT_IN = "not_in"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"
    LENGTH_EQUALS = "length_equals"
    LENGTH_GREATER = "length_greater"
    LENGTH_LESS = "length_less"


@dataclass
class AssertionResult:
    """断言结果数据类"""
    assertion_id: str
    assertion_type: AssertionType
    operator: AssertionOperator
    actual_value: Any
    expected_value: Any
    passed: bool
    message: str
    timestamp: datetime
    execution_time: float  # 执行时间（毫秒）
    context: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 0


@dataclass
class AssertionConfig:
    """断言配置数据类"""
    assertion_type: AssertionType = AssertionType.HARD
    operator: AssertionOperator = AssertionOperator.EQUALS
    expected_value: Any = None
    message: str = ""
    timeout: float = 30.0  # 超时时间（秒）
    retry_count: int = 0
    retry_interval: float = 1.0  # 重试间隔（秒）
    ignore_case: bool = False
    trim_whitespace: bool = True
    custom_validator: Optional[Callable] = None
    context: Dict[str, Any] = field(default_factory=dict)


class AssertionManager:
    """断言管理器"""
    
    def __init__(self):
        self.results: List[AssertionResult] = []
        self.soft_assertion_failures: List[AssertionResult] = []
        self.statistics = {
            'total_assertions': 0,
            'passed_assertions': 0,
            'failed_assertions': 0,
            'soft_failures': 0,
            'hard_failures': 0,
            'retried_assertions': 0
        }
        
    def execute_assertion(self, assertion_id: str, actual_value: Any, config: AssertionConfig) -> AssertionResult:
        """执行断言"""
        start_time = time.time()
        
        try:
            # 预处理值
            processed_actual = self._preprocess_value(actual_value, config)
            processed_expected = self._preprocess_value(config.expected_value, config)
            
            # 执行断言逻辑
            if config.assertion_type == AssertionType.RETRY:
                result = self._execute_retry_assertion(assertion_id, processed_actual, processed_expected, config)
            elif config.assertion_type == AssertionType.TIMEOUT:
                result = self._execute_timeout_assertion(assertion_id, processed_actual, processed_expected, config)
            else:
                result = self._execute_basic_assertion(assertion_id, processed_actual, processed_expected, config)
                
            # 记录执行时间
            result.execution_time = (time.time() - start_time) * 1000
            
            # 更新统计信息
            self._update_statistics(result)
            
            # 存储结果
            self.results.append(result)
            
            # 处理软断言失败
            if not result.passed and config.assertion_type == AssertionType.SOFT:
                self.soft_assertion_failures.append(result)
                logger.warning(f"软断言失败: {result.message}")
            elif not result.passed and config.assertion_type == AssertionType.HARD:
                logger.error(f"硬断言失败: {result.message}")
                raise AssertionError(result.message)
                
            return result
            
        except Exception as e:
            # 创建失败结果
            result = AssertionResult(
                assertion_id=assertion_id,
                assertion_type=config.assertion_type,
                operator=config.operator,
                actual_value=actual_value,
                expected_value=config.expected_value,
                passed=False,
                message=f"断言执行异常: {str(e)}",
                timestamp=datetime.now(),
                execution_time=(time.time() - start_time) * 1000,
                context=config.context
            )
            
            self.results.append(result)
            self._update_statistics(result)
            
            if config.assertion_type == AssertionType.HARD:
                raise
            else:
                self.soft_assertion_failures.append(result)
                return result
                
    def _preprocess_value(self, value: Any, config: AssertionConfig) -> Any:
        """预处理值"""
        if isinstance(value, str):
            if config.trim_whitespace:
                value = value.strip()
            if config.ignore_case:
                value = value.lower()
        return value
        
    def _execute_basic_assertion(self, assertion_id: str, actual: Any, expected: Any, config: AssertionConfig) -> AssertionResult:
        """执行基础断言"""
        passed = False
        message = ""
        
        try:
            # 自定义验证器
            if config.custom_validator:
                passed = config.custom_validator(actual, expected)
                message = config.message or f"自定义验证: {passed}"
            else:
                passed, message = self._evaluate_assertion(actual, expected, config.operator)
                
            if config.message:
                message = config.message
                
        except Exception as e:
            passed = False
            message = f"断言评估异常: {str(e)}"
            
        return AssertionResult(
            assertion_id=assertion_id,
            assertion_type=config.assertion_type,
            operator=config.operator,
            actual_value=actual,
            expected_value=expected,
            passed=passed,
            message=message,
            timestamp=datetime.now(),
            execution_time=0,  # 将在外层设置
            context=config.context
        )
        
    def _execute_retry_assertion(self, assertion_id: str, actual: Any, expected: Any, config: AssertionConfig) -> AssertionResult:
        """执行重试断言"""
        last_result = None
        
        for attempt in range(config.retry_count + 1):
            try:
                result = self._execute_basic_assertion(assertion_id, actual, expected, config)
                result.retry_count = attempt
                result.max_retries = config.retry_count
                
                if result.passed:
                    if attempt > 0:
                        logger.info(f"重试断言成功: {assertion_id}, 尝试次数: {attempt + 1}")
                    return result
                    
                last_result = result
                
                if attempt < config.retry_count:
                    time.sleep(config.retry_interval)
                    
            except Exception as e:
                last_result = AssertionResult(
                    assertion_id=assertion_id,
                    assertion_type=config.assertion_type,
                    operator=config.operator,
                    actual_value=actual,
                    expected_value=expected,
                    passed=False,
                    message=f"重试断言异常: {str(e)}",
                    timestamp=datetime.now(),
                    execution_time=0,
                    context=config.context,
                    retry_count=attempt,
                    max_retries=config.retry_count
                )
                
                if attempt < config.retry_count:
                    time.sleep(config.retry_interval)
                    
        # 所有重试都失败
        if last_result:
            last_result.message = f"重试断言失败: {last_result.message} (尝试 {config.retry_count + 1} 次)"
            
        return last_result
        
    def _execute_timeout_assertion(self, assertion_id: str, actual: Any, expected: Any, config: AssertionConfig) -> AssertionResult:
        """执行超时断言"""
        start_time = time.time()
        last_result = None
        
        while time.time() - start_time < config.timeout:
            try:
                result = self._execute_basic_assertion(assertion_id, actual, expected, config)
                
                if result.passed:
                    elapsed = time.time() - start_time
                    logger.info(f"超时断言成功: {assertion_id}, 耗时: {elapsed:.2f}s")
                    return result
                    
                last_result = result
                time.sleep(0.5)  # 短暂等待后重试
                
            except Exception as e:
                last_result = AssertionResult(
                    assertion_id=assertion_id,
                    assertion_type=config.assertion_type,
                    operator=config.operator,
                    actual_value=actual,
                    expected_value=expected,
                    passed=False,
                    message=f"超时断言异常: {str(e)}",
                    timestamp=datetime.now(),
                    execution_time=0,
                    context=config.context
                )
                time.sleep(0.5)
                
        # 超时失败
        elapsed = time.time() - start_time
        if last_result:
            last_result.message = f"超时断言失败: {last_result.message} (超时: {elapsed:.2f}s)"
            
        return last_result
        
    def _evaluate_assertion(self, actual: Any, expected: Any, operator: AssertionOperator) -> tuple[bool, str]:
        """评估断言"""
        try:
            if operator == AssertionOperator.EQUALS:
                passed = actual == expected
                message = f"期望 '{actual}' 等于 '{expected}'"
                
            elif operator == AssertionOperator.NOT_EQUALS:
                passed = actual != expected
                message = f"期望 '{actual}' 不等于 '{expected}'"
                
            elif operator == AssertionOperator.CONTAINS:
                passed = str(expected) in str(actual)
                message = f"期望 '{actual}' 包含 '{expected}'"
                
            elif operator == AssertionOperator.NOT_CONTAINS:
                passed = str(expected) not in str(actual)
                message = f"期望 '{actual}' 不包含 '{expected}'"
                
            elif operator == AssertionOperator.STARTS_WITH:
                passed = str(actual).startswith(str(expected))
                message = f"期望 '{actual}' 以 '{expected}' 开头"
                
            elif operator == AssertionOperator.ENDS_WITH:
                passed = str(actual).endswith(str(expected))
                message = f"期望 '{actual}' 以 '{expected}' 结尾"
                
            elif operator == AssertionOperator.MATCHES:
                passed = bool(re.search(str(expected), str(actual)))
                message = f"期望 '{actual}' 匹配正则 '{expected}'"
                
            elif operator == AssertionOperator.GREATER_THAN:
                passed = float(actual) > float(expected)
                message = f"期望 {actual} 大于 {expected}"
                
            elif operator == AssertionOperator.LESS_THAN:
                passed = float(actual) < float(expected)
                message = f"期望 {actual} 小于 {expected}"
                
            elif operator == AssertionOperator.GREATER_EQUAL:
                passed = float(actual) >= float(expected)
                message = f"期望 {actual} 大于等于 {expected}"
                
            elif operator == AssertionOperator.LESS_EQUAL:
                passed = float(actual) <= float(expected)
                message = f"期望 {actual} 小于等于 {expected}"
                
            elif operator == AssertionOperator.IN:
                passed = actual in expected
                message = f"期望 '{actual}' 在 '{expected}' 中"
                
            elif operator == AssertionOperator.NOT_IN:
                passed = actual not in expected
                message = f"期望 '{actual}' 不在 '{expected}' 中"
                
            elif operator == AssertionOperator.IS_EMPTY:
                passed = len(str(actual)) == 0 if actual is not None else True
                message = f"期望 '{actual}' 为空"
                
            elif operator == AssertionOperator.IS_NOT_EMPTY:
                passed = len(str(actual)) > 0 if actual is not None else False
                message = f"期望 '{actual}' 不为空"
                
            elif operator == AssertionOperator.IS_NULL:
                passed = actual is None
                message = f"期望 '{actual}' 为 null"
                
            elif operator == AssertionOperator.IS_NOT_NULL:
                passed = actual is not None
                message = f"期望 '{actual}' 不为 null"
                
            elif operator == AssertionOperator.IS_TRUE:
                passed = bool(actual) is True
                message = f"期望 '{actual}' 为 true"
                
            elif operator == AssertionOperator.IS_FALSE:
                passed = bool(actual) is False
                message = f"期望 '{actual}' 为 false"
                
            elif operator == AssertionOperator.LENGTH_EQUALS:
                actual_length = len(actual) if hasattr(actual, '__len__') else 0
                passed = actual_length == int(expected)
                message = f"期望 '{actual}' 长度等于 {expected}, 实际长度: {actual_length}"
                
            elif operator == AssertionOperator.LENGTH_GREATER:
                actual_length = len(actual) if hasattr(actual, '__len__') else 0
                passed = actual_length > int(expected)
                message = f"期望 '{actual}' 长度大于 {expected}, 实际长度: {actual_length}"
                
            elif operator == AssertionOperator.LENGTH_LESS:
                actual_length = len(actual) if hasattr(actual, '__len__') else 0
                passed = actual_length < int(expected)
                message = f"期望 '{actual}' 长度小于 {expected}, 实际长度: {actual_length}"
                
            else:
                passed = False
                message = f"不支持的断言操作符: {operator}"
                
            return passed, message
            
        except Exception as e:
            return False, f"断言评估异常: {str(e)}"
            
    def _update_statistics(self, result: AssertionResult):
        """更新统计信息"""
        self.statistics['total_assertions'] += 1
        
        if result.passed:
            self.statistics['passed_assertions'] += 1
        else:
            self.statistics['failed_assertions'] += 1
            
            if result.assertion_type == AssertionType.SOFT:
                self.statistics['soft_failures'] += 1
            else:
                self.statistics['hard_failures'] += 1
                
        if result.retry_count > 0:
            self.statistics['retried_assertions'] += 1
            
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.statistics.copy()
        
        if stats['total_assertions'] > 0:
            stats['pass_rate'] = stats['passed_assertions'] / stats['total_assertions'] * 100
            stats['fail_rate'] = stats['failed_assertions'] / stats['total_assertions'] * 100
        else:
            stats['pass_rate'] = 0
            stats['fail_rate'] = 0
            
        return stats
        
    def get_failed_assertions(self, assertion_type: Optional[AssertionType] = None) -> List[AssertionResult]:
        """获取失败的断言"""
        failed = [r for r in self.results if not r.passed]
        
        if assertion_type:
            failed = [r for r in failed if r.assertion_type == assertion_type]
            
        return failed
        
    def reset_statistics(self):
        """重置统计信息"""
        self.results.clear()
        self.soft_assertion_failures.clear()
        self.statistics = {
            'total_assertions': 0,
            'passed_assertions': 0,
            'failed_assertions': 0,
            'soft_failures': 0,
            'hard_failures': 0,
            'retried_assertions': 0
        }
        
    def check_soft_assertions(self) -> bool:
        """检查软断言是否有失败"""
        if self.soft_assertion_failures:
            failure_messages = [f.message for f in self.soft_assertion_failures]
            raise AssertionError(f"软断言失败 ({len(self.soft_assertion_failures)} 个): {'; '.join(failure_messages)}")
        return True


class AssertionCommandsPlugin:
    """断言命令插件"""
    
    def __init__(self):
        self.name = "assertion_commands"
        self.version = "1.0.0"
        self.description = "增强的断言命令插件"
        
        # 断言管理器
        self.assertion_manager = AssertionManager()
        
        # 注册命令
        self._register_commands()
        
    def _register_commands(self):
        """注册断言命令"""
        commands = {
            'ASSERT_EQUALS': AssertEqualsCommand,
            'ASSERT_NOT_EQUALS': AssertNotEqualsCommand,
            'ASSERT_CONTAINS': AssertContainsCommand,
            'ASSERT_NOT_CONTAINS': AssertNotContainsCommand,
            'ASSERT_STARTS_WITH': AssertStartsWithCommand,
            'ASSERT_ENDS_WITH': AssertEndsWithCommand,
            'ASSERT_MATCHES': AssertMatchesCommand,
            'ASSERT_GREATER_THAN': AssertGreaterThanCommand,
            'ASSERT_LESS_THAN': AssertLessThanCommand,
            'ASSERT_IN': AssertInCommand,
            'ASSERT_NOT_IN': AssertNotInCommand,
            'ASSERT_EMPTY': AssertEmptyCommand,
            'ASSERT_NOT_EMPTY': AssertNotEmptyCommand,
            'ASSERT_NULL': AssertNullCommand,
            'ASSERT_NOT_NULL': AssertNotNullCommand,
            'ASSERT_TRUE': AssertTrueCommand,
            'ASSERT_FALSE': AssertFalseCommand,
            'ASSERT_LENGTH': AssertLengthCommand,
            'SOFT_ASSERT': SoftAssertCommand,
            'HARD_ASSERT': HardAssertCommand,
            'CONDITIONAL_ASSERT': ConditionalAssertCommand,
            'BATCH_ASSERT': BatchAssertCommand,
            'RETRY_ASSERT': RetryAssertCommand,
            'TIMEOUT_ASSERT': TimeoutAssertCommand,
            'CUSTOM_ASSERT': CustomAssertCommand,
            'CHECK_SOFT_ASSERTIONS': CheckSoftAssertionsCommand,
            'GET_ASSERTION_STATS': GetAssertionStatsCommand,
            'RESET_ASSERTION_STATS': ResetAssertionStatsCommand
        }
        
        for action_name, command_class in commands.items():
            try:
                # 动态创建StepAction属性
                if not hasattr(StepAction, action_name):
                    setattr(StepAction, action_name, [action_name.lower(), action_name.lower().replace('_', ' ')])
                
                action = getattr(StepAction, action_name)
                CommandFactory.register(action)(command_class)
                logger.info(f"已注册断言命令: {action_name}")
            except Exception as e:
                logger.error(f"注册断言命令失败 {action_name}: {e}")


# 全局断言管理器实例
_assertion_manager = AssertionManager()


# 基础断言命令
class BaseAssertCommand(Command):
    """基础断言命令"""
    
    def __init__(self):
        super().__init__()
        self.assertion_manager = _assertion_manager
        
    def create_assertion_config(self, step: Dict[str, Any], operator: AssertionOperator, assertion_type: AssertionType = AssertionType.HARD) -> AssertionConfig:
        """创建断言配置"""
        return AssertionConfig(
            assertion_type=AssertionType(step.get('assertion_type', assertion_type.value)),
            operator=operator,
            expected_value=step.get('expected_value'),
            message=step.get('message', ''),
            timeout=step.get('timeout', 30.0),
            retry_count=step.get('retry_count', 0),
            retry_interval=step.get('retry_interval', 1.0),
            ignore_case=step.get('ignore_case', False),
            trim_whitespace=step.get('trim_whitespace', True),
            context=step.get('context', {})
        )


# 具体断言命令实现
@CommandFactory.register(StepAction.ASSERT_EQUALS)
class AssertEqualsCommand(BaseAssertCommand):
    """等于断言命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_equals_{int(time.time() * 1000)}")
        expected_value = step.get('expected_value', value)
        
        # 获取实际值
        if selector:
            actual_value = ui_helper.get_element_text(selector)
        else:
            actual_value = step.get('actual_value')
            
        config = self.create_assertion_config(step, AssertionOperator.EQUALS)
        config.expected_value = expected_value
        
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.ASSERT_NOT_EQUALS)
class AssertNotEqualsCommand(BaseAssertCommand):
    """不等于断言命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_not_equals_{int(time.time() * 1000)}")
        expected_value = step.get('expected_value', value)
        
        if selector:
            actual_value = ui_helper.get_element_text(selector)
        else:
            actual_value = step.get('actual_value')
            
        config = self.create_assertion_config(step, AssertionOperator.NOT_EQUALS)
        config.expected_value = expected_value
        
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.ASSERT_CONTAINS)
class AssertContainsCommand(BaseAssertCommand):
    """包含断言命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_contains_{int(time.time() * 1000)}")
        expected_value = step.get('expected_value', value)
        
        if selector:
            actual_value = ui_helper.get_element_text(selector)
        else:
            actual_value = step.get('actual_value')
            
        config = self.create_assertion_config(step, AssertionOperator.CONTAINS)
        config.expected_value = expected_value
        
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.ASSERT_NOT_CONTAINS)
class AssertNotContainsCommand(BaseAssertCommand):
    """不包含断言命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_not_contains_{int(time.time() * 1000)}")
        expected_value = step.get('expected_value', value)
        
        if selector:
            actual_value = ui_helper.get_element_text(selector)
        else:
            actual_value = step.get('actual_value')
            
        config = self.create_assertion_config(step, AssertionOperator.NOT_CONTAINS)
        config.expected_value = expected_value
        
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.SOFT_ASSERT)
class SoftAssertCommand(BaseAssertCommand):
    """软断言命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"soft_assert_{int(time.time() * 1000)}")
        operator = AssertionOperator(step.get('operator', 'equals'))
        expected_value = step.get('expected_value', value)
        
        if selector:
            actual_value = ui_helper.get_element_text(selector)
        else:
            actual_value = step.get('actual_value')
            
        config = self.create_assertion_config(step, operator, AssertionType.SOFT)
        config.expected_value = expected_value
        
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.HARD_ASSERT)
class HardAssertCommand(BaseAssertCommand):
    """硬断言命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"hard_assert_{int(time.time() * 1000)}")
        operator = AssertionOperator(step.get('operator', 'equals'))
        expected_value = step.get('expected_value', value)
        
        if selector:
            actual_value = ui_helper.get_element_text(selector)
        else:
            actual_value = step.get('actual_value')
            
        config = self.create_assertion_config(step, operator, AssertionType.HARD)
        config.expected_value = expected_value
        
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.RETRY_ASSERT)
class RetryAssertCommand(BaseAssertCommand):
    """重试断言命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"retry_assert_{int(time.time() * 1000)}")
        operator = AssertionOperator(step.get('operator', 'equals'))
        expected_value = step.get('expected_value', value)
        
        if selector:
            actual_value = ui_helper.get_element_text(selector)
        else:
            actual_value = step.get('actual_value')
            
        config = self.create_assertion_config(step, operator, AssertionType.RETRY)
        config.expected_value = expected_value
        
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.CHECK_SOFT_ASSERTIONS)
class CheckSoftAssertionsCommand(BaseAssertCommand):
    """检查软断言命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        try:
            self.assertion_manager.check_soft_assertions()
            logger.info("所有软断言检查通过")
            
            if step.get('variable_name'):
                ui_helper.store_variable(step['variable_name'], True, step.get('scope', 'global'))
                
        except AssertionError as e:
            logger.error(f"软断言检查失败: {e}")
            
            if step.get('variable_name'):
                ui_helper.store_variable(step['variable_name'], False, step.get('scope', 'global'))
                
            if step.get('fail_on_soft_assertion', True):
                raise


@CommandFactory.register(StepAction.GET_ASSERTION_STATS)
class GetAssertionStatsCommand(BaseAssertCommand):
    """获取断言统计命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        stats = self.assertion_manager.get_statistics()
        
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], stats, step.get('scope', 'global'))
            
        logger.info(f"断言统计: 总计 {stats['total_assertions']}, 通过 {stats['passed_assertions']}, 失败 {stats['failed_assertions']}")


@CommandFactory.register(StepAction.RESET_ASSERTION_STATS)
class ResetAssertionStatsCommand(BaseAssertCommand):
    """重置断言统计命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        self.assertion_manager.reset_statistics()
        logger.info("断言统计已重置")


# 其他断言命令的简化实现（为了节省空间，这里只展示几个关键的）
@CommandFactory.register(StepAction.ASSERT_STARTS_WITH)
class AssertStartsWithCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_starts_with_{int(time.time() * 1000)}")
        expected_value = step.get('expected_value', value)
        actual_value = ui_helper.get_element_text(selector) if selector else step.get('actual_value')
        config = self.create_assertion_config(step, AssertionOperator.STARTS_WITH)
        config.expected_value = expected_value
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.ASSERT_ENDS_WITH)
class AssertEndsWithCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_ends_with_{int(time.time() * 1000)}")
        expected_value = step.get('expected_value', value)
        actual_value = ui_helper.get_element_text(selector) if selector else step.get('actual_value')
        config = self.create_assertion_config(step, AssertionOperator.ENDS_WITH)
        config.expected_value = expected_value
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.ASSERT_MATCHES)
class AssertMatchesCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_matches_{int(time.time() * 1000)}")
        expected_value = step.get('expected_value', value)
        actual_value = ui_helper.get_element_text(selector) if selector else step.get('actual_value')
        config = self.create_assertion_config(step, AssertionOperator.MATCHES)
        config.expected_value = expected_value
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.ASSERT_GREATER_THAN)
class AssertGreaterThanCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_greater_than_{int(time.time() * 1000)}")
        expected_value = step.get('expected_value', value)
        actual_value = ui_helper.get_element_text(selector) if selector else step.get('actual_value')
        config = self.create_assertion_config(step, AssertionOperator.GREATER_THAN)
        config.expected_value = expected_value
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.ASSERT_LESS_THAN)
class AssertLessThanCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_less_than_{int(time.time() * 1000)}")
        expected_value = step.get('expected_value', value)
        actual_value = ui_helper.get_element_text(selector) if selector else step.get('actual_value')
        config = self.create_assertion_config(step, AssertionOperator.LESS_THAN)
        config.expected_value = expected_value
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.ASSERT_IN)
class AssertInCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_in_{int(time.time() * 1000)}")
        expected_value = step.get('expected_value', value)
        actual_value = ui_helper.get_element_text(selector) if selector else step.get('actual_value')
        config = self.create_assertion_config(step, AssertionOperator.IN)
        config.expected_value = expected_value
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.ASSERT_NOT_IN)
class AssertNotInCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_not_in_{int(time.time() * 1000)}")
        expected_value = step.get('expected_value', value)
        actual_value = ui_helper.get_element_text(selector) if selector else step.get('actual_value')
        config = self.create_assertion_config(step, AssertionOperator.NOT_IN)
        config.expected_value = expected_value
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.ASSERT_EMPTY)
class AssertEmptyCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_empty_{int(time.time() * 1000)}")
        actual_value = ui_helper.get_element_text(selector) if selector else step.get('actual_value')
        config = self.create_assertion_config(step, AssertionOperator.IS_EMPTY)
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.ASSERT_NOT_EMPTY)
class AssertNotEmptyCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_not_empty_{int(time.time() * 1000)}")
        actual_value = ui_helper.get_element_text(selector) if selector else step.get('actual_value')
        config = self.create_assertion_config(step, AssertionOperator.IS_NOT_EMPTY)
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.ASSERT_NULL)
class AssertNullCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_null_{int(time.time() * 1000)}")
        actual_value = ui_helper.get_element_text(selector) if selector else step.get('actual_value')
        config = self.create_assertion_config(step, AssertionOperator.IS_NULL)
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.ASSERT_NOT_NULL)
class AssertNotNullCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_not_null_{int(time.time() * 1000)}")
        actual_value = ui_helper.get_element_text(selector) if selector else step.get('actual_value')
        config = self.create_assertion_config(step, AssertionOperator.IS_NOT_NULL)
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.ASSERT_TRUE)
class AssertTrueCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_true_{int(time.time() * 1000)}")
        actual_value = ui_helper.get_element_text(selector) if selector else step.get('actual_value')
        config = self.create_assertion_config(step, AssertionOperator.IS_TRUE)
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.ASSERT_FALSE)
class AssertFalseCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_false_{int(time.time() * 1000)}")
        actual_value = ui_helper.get_element_text(selector) if selector else step.get('actual_value')
        config = self.create_assertion_config(step, AssertionOperator.IS_FALSE)
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.ASSERT_LENGTH)
class AssertLengthCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"assert_length_{int(time.time() * 1000)}")
        expected_length = step.get('expected_length', value)
        operator_str = step.get('length_operator', 'equals')
        
        # 确定长度操作符
        if operator_str == 'equals':
            operator = AssertionOperator.LENGTH_EQUALS
        elif operator_str == 'greater':
            operator = AssertionOperator.LENGTH_GREATER
        elif operator_str == 'less':
            operator = AssertionOperator.LENGTH_LESS
        else:
            operator = AssertionOperator.LENGTH_EQUALS
            
        actual_value = ui_helper.get_element_text(selector) if selector else step.get('actual_value')
        config = self.create_assertion_config(step, operator)
        config.expected_value = expected_length
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.CONDITIONAL_ASSERT)
class ConditionalAssertCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        condition = step.get('condition')
        if not condition:
            logger.info("条件断言跳过：未指定条件")
            return
            
        # 评估条件
        try:
            condition_result = eval(condition, {}, ui_helper.get_all_variables())
            if not condition_result:
                logger.info(f"条件断言跳过：条件不满足 - {condition}")
                return
        except Exception as e:
            logger.error(f"条件断言条件评估失败: {e}")
            return
            
        # 执行断言
        assertion_id = step.get('assertion_id', f"conditional_assert_{int(time.time() * 1000)}")
        operator = AssertionOperator(step.get('operator', 'equals'))
        expected_value = step.get('expected_value', value)
        actual_value = ui_helper.get_element_text(selector) if selector else step.get('actual_value')
        
        config = self.create_assertion_config(step, operator, AssertionType.CONDITIONAL)
        config.expected_value = expected_value
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.BATCH_ASSERT)
class BatchAssertCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertions = step.get('assertions', [])
        if not assertions:
            logger.warning("批量断言：未指定断言列表")
            return
            
        results = []
        for i, assertion in enumerate(assertions):
            try:
                assertion_id = assertion.get('assertion_id', f"batch_assert_{i}_{int(time.time() * 1000)}")
                operator = AssertionOperator(assertion.get('operator', 'equals'))
                expected_value = assertion.get('expected_value')
                actual_value = assertion.get('actual_value')
                
                if assertion.get('selector'):
                    actual_value = ui_helper.get_element_text(assertion['selector'])
                    
                config = self.create_assertion_config(assertion, operator, AssertionType.BATCH)
                config.expected_value = expected_value
                result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
                results.append(result)
                
            except Exception as e:
                logger.error(f"批量断言第 {i+1} 项执行失败: {e}")
                
        # 存储批量断言结果
        if step.get('variable_name'):
            batch_result = {
                'total': len(results),
                'passed': sum(1 for r in results if r.passed),
                'failed': sum(1 for r in results if not r.passed),
                'results': [{'id': r.assertion_id, 'passed': r.passed, 'message': r.message} for r in results]
            }
            ui_helper.store_variable(step['variable_name'], batch_result, step.get('scope', 'global'))


@CommandFactory.register(StepAction.TIMEOUT_ASSERT)
class TimeoutAssertCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"timeout_assert_{int(time.time() * 1000)}")
        operator = AssertionOperator(step.get('operator', 'equals'))
        expected_value = step.get('expected_value', value)
        
        # 对于超时断言，我们需要在循环中获取实际值
        def get_actual_value():
            if selector:
                return ui_helper.get_element_text(selector)
            else:
                return step.get('actual_value')
                
        config = self.create_assertion_config(step, operator, AssertionType.TIMEOUT)
        config.expected_value = expected_value
        
        # 执行超时断言（实际值在超时断言内部获取）
        result = self.assertion_manager.execute_assertion(assertion_id, get_actual_value(), config)
        
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


@CommandFactory.register(StepAction.CUSTOM_ASSERT)
class CustomAssertCommand(BaseAssertCommand):
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        assertion_id = step.get('assertion_id', f"custom_assert_{int(time.time() * 1000)}")
        validator_code = step.get('validator')
        
        if not validator_code:
            logger.error("自定义断言：未指定验证器代码")
            return
            
        actual_value = ui_helper.get_element_text(selector) if selector else step.get('actual_value')
        expected_value = step.get('expected_value', value)
        
        # 创建自定义验证器
        def custom_validator(actual, expected):
            try:
                # 创建执行上下文
                context = {
                    'actual': actual,
                    'expected': expected,
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    're': re,
                    'json': json
                }
                context.update(ui_helper.get_all_variables())
                
                # 执行验证器代码
                return eval(validator_code, {}, context)
            except Exception as e:
                logger.error(f"自定义验证器执行失败: {e}")
                return False
                
        config = self.create_assertion_config(step, AssertionOperator.EQUALS)  # 操作符在自定义断言中不重要
        config.expected_value = expected_value
        config.custom_validator = custom_validator
        
        result = self.assertion_manager.execute_assertion(assertion_id, actual_value, config)
        
        if step.get('variable_name'):
            ui_helper.store_variable(step['variable_name'], result.passed, step.get('scope', 'global'))


def plugin_init():
    """插件初始化函数"""
    plugin = AssertionCommandsPlugin()
    logger.info(f"断言命令插件已初始化: {plugin.name} v{plugin.version}")
    return plugin


def plugin_cleanup():
    """插件清理函数"""
    global _assertion_manager
    _assertion_manager.reset_statistics()
    logger.info("断言命令插件已清理")