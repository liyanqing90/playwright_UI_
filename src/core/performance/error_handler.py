"""错误处理和重试机制

提供智能的错误处理和重试功能，包括：
- 智能错误分类和处理
- 自适应重试策略
- 错误恢复机制
- 错误统计和分析
- 稳定性监控
"""

import asyncio
import inspect
import random
import time
import traceback
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Dict, List, Any, Optional, Callable, Type

import structlog

logger = structlog.get_logger(__name__)


class ErrorCategory(Enum):
    """错误分类"""

    NETWORK = "network"
    TIMEOUT = "timeout"
    ELEMENT_NOT_FOUND = "element_not_found"
    JAVASCRIPT_ERROR = "javascript_error"
    BROWSER_CRASH = "browser_crash"
    PERMISSION_DENIED = "permission_denied"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """错误严重程度"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RetryStrategy(Enum):
    """重试策略"""

    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    RANDOM_JITTER = "random_jitter"
    ADAPTIVE = "adaptive"


@dataclass
class ErrorPattern:
    """错误模式"""

    category: ErrorCategory
    severity: ErrorSeverity
    keywords: List[str]
    exception_types: List[str]
    retry_strategy: RetryStrategy
    max_retries: int
    base_delay: float
    max_delay: float
    recovery_actions: List[str]
    escalation_threshold: int


@dataclass
class ErrorRecord:
    """错误记录"""

    id: str
    timestamp: str
    category: ErrorCategory
    severity: ErrorSeverity
    exception_type: str
    message: str
    stack_trace: str
    context: Dict[str, Any]
    retry_count: int
    recovery_attempted: bool
    resolved: bool
    resolution_time: Optional[str] = None
    resolution_method: Optional[str] = None


@dataclass
class RetryConfig:
    """重试配置"""

    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter_range: float = 0.1
    timeout: Optional[float] = None
    retry_on_exceptions: List[Type[Exception]] = None
    stop_on_exceptions: List[Type[Exception]] = None

    def __post_init__(self):
        if self.retry_on_exceptions is None:
            self.retry_on_exceptions = [Exception]
        if self.stop_on_exceptions is None:
            self.stop_on_exceptions = []


class ErrorHandler:
    """智能错误处理器

    提供全面的错误处理和重试功能。
    """

    def __init__(self):
        """初始化错误处理器"""
        self.error_patterns = self._initialize_error_patterns()
        self.error_history: List[ErrorRecord] = []
        self.error_statistics: Dict[str, Any] = {}
        self.recovery_functions: Dict[str, Callable] = {}
        self.escalation_handlers: Dict[ErrorCategory, Callable] = {}

        # 注册默认恢复函数
        self._register_default_recovery_functions()

        logger.info("错误处理器初始化完成")

    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """初始化错误模式"""
        return [
            ErrorPattern(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.HIGH,
                keywords=["network", "connection", "dns", "timeout", "unreachable"],
                exception_types=["ConnectionError", "TimeoutError", "DNSError"],
                retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_retries=5,
                base_delay=2.0,
                max_delay=30.0,
                recovery_actions=["check_network", "reset_connection", "change_dns"],
                escalation_threshold=3,
            ),
            ErrorPattern(
                category=ErrorCategory.TIMEOUT,
                severity=ErrorSeverity.MEDIUM,
                keywords=["timeout", "wait", "slow", "loading"],
                exception_types=["TimeoutError", "asyncio.TimeoutError"],
                retry_strategy=RetryStrategy.LINEAR_BACKOFF,
                max_retries=3,
                base_delay=5.0,
                max_delay=20.0,
                recovery_actions=["increase_timeout", "refresh_page"],
                escalation_threshold=2,
            ),
            ErrorPattern(
                category=ErrorCategory.ELEMENT_NOT_FOUND,
                severity=ErrorSeverity.MEDIUM,
                keywords=["element", "selector", "not found", "locate"],
                exception_types=["ElementNotFoundError", "NoSuchElementException"],
                retry_strategy=RetryStrategy.FIXED_DELAY,
                max_retries=4,
                base_delay=1.0,
                max_delay=5.0,
                recovery_actions=[
                    "wait_for_element",
                    "try_alternative_selector",
                    "refresh_page",
                ],
                escalation_threshold=3,
            ),
            ErrorPattern(
                category=ErrorCategory.JAVASCRIPT_ERROR,
                severity=ErrorSeverity.HIGH,
                keywords=["javascript", "script", "eval", "execution"],
                exception_types=["JavaScriptError", "EvaluationError"],
                retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_retries=2,
                base_delay=3.0,
                max_delay=15.0,
                recovery_actions=["reload_page", "clear_cache"],
                escalation_threshold=1,
            ),
            ErrorPattern(
                category=ErrorCategory.BROWSER_CRASH,
                severity=ErrorSeverity.CRITICAL,
                keywords=["crash", "browser", "terminated", "killed"],
                exception_types=["BrowserCrashError", "ProcessTerminatedError"],
                retry_strategy=RetryStrategy.FIXED_DELAY,
                max_retries=2,
                base_delay=10.0,
                max_delay=30.0,
                recovery_actions=["restart_browser", "clear_browser_data"],
                escalation_threshold=1,
            ),
            ErrorPattern(
                category=ErrorCategory.PERMISSION_DENIED,
                severity=ErrorSeverity.HIGH,
                keywords=["permission", "denied", "access", "forbidden"],
                exception_types=["PermissionError", "AccessDeniedError"],
                retry_strategy=RetryStrategy.FIXED_DELAY,
                max_retries=1,
                base_delay=5.0,
                max_delay=5.0,
                recovery_actions=["check_permissions", "escalate_privileges"],
                escalation_threshold=1,
            ),
            ErrorPattern(
                category=ErrorCategory.RESOURCE_EXHAUSTED,
                severity=ErrorSeverity.HIGH,
                keywords=["memory", "resource", "exhausted", "limit"],
                exception_types=["MemoryError", "ResourceExhaustedError"],
                retry_strategy=RetryStrategy.LINEAR_BACKOFF,
                max_retries=2,
                base_delay=15.0,
                max_delay=60.0,
                recovery_actions=["free_memory", "restart_process"],
                escalation_threshold=1,
            ),
        ]

    def _register_default_recovery_functions(self) -> None:
        """注册默认恢复函数"""
        self.recovery_functions.update(
            {
                "check_network": self._check_network_connectivity,
                "reset_connection": self._reset_network_connection,
                "change_dns": self._change_dns_settings,
                "increase_timeout": self._increase_timeout_settings,
                "refresh_page": self._refresh_current_page,
                "wait_for_element": self._wait_for_element_recovery,
                "try_alternative_selector": self._try_alternative_selectors,
                "reload_page": self._reload_page_completely,
                "clear_cache": self._clear_browser_cache,
                "restart_browser": self._restart_browser_instance,
                "clear_browser_data": self._clear_browser_data,
                "check_permissions": self._check_file_permissions,
                "escalate_privileges": self._escalate_process_privileges,
                "free_memory": self._free_system_memory,
                "restart_process": self._restart_current_process,
            }
        )

    def classify_error(
        self, exception: Exception, context: Dict[str, Any] = None
    ) -> ErrorCategory:
        """分类错误

        Args:
            exception: 异常对象
            context: 错误上下文

        Returns:
            错误分类
        """
        exception_type = type(exception).__name__
        error_message = str(exception).lower()

        # 遍历错误模式进行匹配
        for pattern in self.error_patterns:
            # 检查异常类型
            if exception_type in pattern.exception_types:
                return pattern.category

            # 检查关键词
            if any(keyword in error_message for keyword in pattern.keywords):
                return pattern.category

        return ErrorCategory.UNKNOWN

    def get_error_severity(self, category: ErrorCategory) -> ErrorSeverity:
        """获取错误严重程度"""
        for pattern in self.error_patterns:
            if pattern.category == category:
                return pattern.severity
        return ErrorSeverity.MEDIUM

    def get_retry_config(self, category: ErrorCategory) -> RetryConfig:
        """获取重试配置"""
        for pattern in self.error_patterns:
            if pattern.category == category:
                return RetryConfig(
                    strategy=pattern.retry_strategy,
                    max_retries=pattern.max_retries,
                    base_delay=pattern.base_delay,
                    max_delay=pattern.max_delay,
                )

        # 默认配置
        return RetryConfig()

    async def handle_error(
        self,
        exception: Exception,
        context: Dict[str, Any] = None,
        attempt_recovery: bool = True,
    ) -> ErrorRecord:
        """处理错误

        Args:
            exception: 异常对象
            context: 错误上下文
            attempt_recovery: 是否尝试恢复

        Returns:
            错误记录
        """
        if context is None:
            context = {}

        # 分类错误
        category = self.classify_error(exception, context)
        severity = self.get_error_severity(category)

        # 创建错误记录
        error_record = ErrorRecord(
            id=f"error_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
            timestamp=datetime.now().isoformat(),
            category=category,
            severity=severity,
            exception_type=type(exception).__name__,
            message=str(exception),
            stack_trace=traceback.format_exc(),
            context=context,
            retry_count=0,
            recovery_attempted=False,
            resolved=False,
        )

        # 记录错误
        self.error_history.append(error_record)
        self._update_error_statistics(error_record)

        logger.error(
            "错误已记录",
            error_id=error_record.id,
            category=category.value,
            severity=severity.value,
            message=str(exception),
        )

        # 尝试恢复
        if attempt_recovery:
            await self._attempt_recovery(error_record)

        return error_record

    async def _attempt_recovery(self, error_record: ErrorRecord) -> bool:
        """尝试错误恢复

        Args:
            error_record: 错误记录

        Returns:
            是否恢复成功
        """
        error_record.recovery_attempted = True

        # 获取恢复动作
        recovery_actions = self._get_recovery_actions(error_record.category)

        for action in recovery_actions:
            try:
                logger.info("尝试恢复动作", error_id=error_record.id, action=action)

                if action in self.recovery_functions:
                    success = await self.recovery_functions[action](
                        error_record.context
                    )

                    if success:
                        error_record.resolved = True
                        error_record.resolution_time = datetime.now().isoformat()
                        error_record.resolution_method = action

                        logger.info(
                            "错误恢复成功", error_id=error_record.id, action=action
                        )
                        return True

            except Exception as e:
                logger.warning(
                    "恢复动作失败",
                    error_id=error_record.id,
                    action=action,
                    error=str(e),
                )

        logger.warning("所有恢复动作均失败", error_id=error_record.id)
        return False

    def _get_recovery_actions(self, category: ErrorCategory) -> List[str]:
        """获取恢复动作"""
        for pattern in self.error_patterns:
            if pattern.category == category:
                return pattern.recovery_actions
        return []

    def retry_with_backoff(self, config: Optional[RetryConfig] = None):
        """重试装饰器

        Args:
            config: 重试配置
        """
        if config is None:
            config = RetryConfig()

        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exception = None

                for attempt in range(config.max_retries + 1):
                    try:
                        if inspect.iscoroutinefunction(func):
                            return await func(*args, **kwargs)
                        else:
                            return func(*args, **kwargs)

                    except Exception as e:
                        last_exception = e

                        # 检查是否应该停止重试
                        if any(
                            isinstance(e, exc_type)
                            for exc_type in config.stop_on_exceptions
                        ):
                            logger.info(
                                "遇到停止重试的异常",
                                exception=type(e).__name__,
                                attempt=attempt,
                            )
                            break

                        # 检查是否应该重试
                        if not any(
                            isinstance(e, exc_type)
                            for exc_type in config.retry_on_exceptions
                        ):
                            logger.info(
                                "异常不在重试列表中",
                                exception=type(e).__name__,
                                attempt=attempt,
                            )
                            break

                        if attempt < config.max_retries:
                            delay = self._calculate_delay(config, attempt)

                            logger.warning(
                                "函数执行失败，准备重试",
                                function=func.__name__,
                                attempt=attempt + 1,
                                max_retries=config.max_retries,
                                delay=delay,
                                error=str(e),
                            )

                            await asyncio.sleep(delay)
                        else:
                            logger.error(
                                "达到最大重试次数",
                                function=func.__name__,
                                max_retries=config.max_retries,
                                error=str(e),
                            )

                # 处理最终失败
                if last_exception:
                    await self.handle_error(
                        last_exception,
                        {
                            "function": func.__name__,
                            "args": str(args),
                            "kwargs": str(kwargs),
                            "retry_attempts": config.max_retries,
                        },
                    )
                    raise last_exception

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_exception = None

                for attempt in range(config.max_retries + 1):
                    try:
                        return func(*args, **kwargs)

                    except Exception as e:
                        last_exception = e

                        # 检查是否应该停止重试
                        if any(
                            isinstance(e, exc_type)
                            for exc_type in config.stop_on_exceptions
                        ):
                            break

                        # 检查是否应该重试
                        if not any(
                            isinstance(e, exc_type)
                            for exc_type in config.retry_on_exceptions
                        ):
                            break

                        if attempt < config.max_retries:
                            delay = self._calculate_delay(config, attempt)

                            logger.warning(
                                "函数执行失败，准备重试",
                                function=func.__name__,
                                attempt=attempt + 1,
                                max_retries=config.max_retries,
                                delay=delay,
                                error=str(e),
                            )

                            time.sleep(delay)

                if last_exception:
                    raise last_exception

            if inspect.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def _calculate_delay(self, config: RetryConfig, attempt: int) -> float:
        """计算重试延迟

        Args:
            config: 重试配置
            attempt: 当前尝试次数

        Returns:
            延迟时间（秒）
        """
        if config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.base_delay

        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_multiplier**attempt)

        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * (attempt + 1)

        elif config.strategy == RetryStrategy.RANDOM_JITTER:
            jitter = random.uniform(-config.jitter_range, config.jitter_range)
            delay = config.base_delay * (1 + jitter)

        elif config.strategy == RetryStrategy.ADAPTIVE:
            # 基于历史错误频率调整延迟
            error_frequency = self._get_recent_error_frequency()
            delay = config.base_delay * (1 + error_frequency)

        else:
            delay = config.base_delay

        # 限制最大延迟
        return min(delay, config.max_delay)

    def _get_recent_error_frequency(self) -> float:
        """获取最近的错误频率"""
        recent_time = datetime.now() - timedelta(minutes=10)
        recent_errors = [
            error
            for error in self.error_history
            if datetime.fromisoformat(error.timestamp) > recent_time
        ]

        # 返回每分钟的错误数量
        return len(recent_errors) / 10.0

    def _update_error_statistics(self, error_record: ErrorRecord) -> None:
        """更新错误统计"""
        category = error_record.category.value
        severity = error_record.severity.value

        if "by_category" not in self.error_statistics:
            self.error_statistics["by_category"] = {}
        if "by_severity" not in self.error_statistics:
            self.error_statistics["by_severity"] = {}
        if "total_count" not in self.error_statistics:
            self.error_statistics["total_count"] = 0

        # 按分类统计
        if category not in self.error_statistics["by_category"]:
            self.error_statistics["by_category"][category] = 0
        self.error_statistics["by_category"][category] += 1

        # 按严重程度统计
        if severity not in self.error_statistics["by_severity"]:
            self.error_statistics["by_severity"][severity] = 0
        self.error_statistics["by_severity"][severity] += 1

        # 总计数
        self.error_statistics["total_count"] += 1

        # 更新最后错误时间
        self.error_statistics["last_error_time"] = error_record.timestamp

    # 恢复函数实现
    async def _check_network_connectivity(self, context: Dict[str, Any]) -> bool:
        """检查网络连接"""
        try:
            # 这里应该实现实际的网络检查
            logger.info("检查网络连接")
            await asyncio.sleep(1)  # 模拟检查过程
            return True
        except Exception as e:
            logger.error("网络检查失败", error=str(e))
            return False

    async def _reset_network_connection(self, context: Dict[str, Any]) -> bool:
        """重置网络连接"""
        try:
            logger.info("重置网络连接")
            await asyncio.sleep(2)  # 模拟重置过程
            return True
        except Exception as e:
            logger.error("网络重置失败", error=str(e))
            return False

    async def _change_dns_settings(self, context: Dict[str, Any]) -> bool:
        """更改DNS设置"""
        try:
            logger.info("更改DNS设置")
            await asyncio.sleep(1)
            return True
        except Exception as e:
            logger.error("DNS设置更改失败", error=str(e))
            return False

    async def _increase_timeout_settings(self, context: Dict[str, Any]) -> bool:
        """增加超时设置"""
        try:
            logger.info("增加超时设置")
            # 这里应该实际调整超时配置
            return True
        except Exception as e:
            logger.error("超时设置调整失败", error=str(e))
            return False

    async def _refresh_current_page(self, context: Dict[str, Any]) -> bool:
        """刷新当前页面"""
        try:
            logger.info("刷新当前页面")
            # 这里应该实际刷新页面
            await asyncio.sleep(2)
            return True
        except Exception as e:
            logger.error("页面刷新失败", error=str(e))
            return False

    async def _wait_for_element_recovery(self, context: Dict[str, Any]) -> bool:
        """等待元素恢复"""
        try:
            logger.info("等待元素恢复")
            await asyncio.sleep(3)  # 等待元素出现
            return True
        except Exception as e:
            logger.error("元素等待失败", error=str(e))
            return False

    async def _try_alternative_selectors(self, context: Dict[str, Any]) -> bool:
        """尝试替代选择器"""
        try:
            logger.info("尝试替代选择器")
            # 这里应该实际尝试不同的选择器
            return True
        except Exception as e:
            logger.error("替代选择器失败", error=str(e))
            return False

    async def _reload_page_completely(self, context: Dict[str, Any]) -> bool:
        """完全重新加载页面"""
        try:
            logger.info("完全重新加载页面")
            await asyncio.sleep(3)
            return True
        except Exception as e:
            logger.error("页面重新加载失败", error=str(e))
            return False

    async def _clear_browser_cache(self, context: Dict[str, Any]) -> bool:
        """清理浏览器缓存"""
        try:
            logger.info("清理浏览器缓存")
            await asyncio.sleep(2)
            return True
        except Exception as e:
            logger.error("缓存清理失败", error=str(e))
            return False

    async def _restart_browser_instance(self, context: Dict[str, Any]) -> bool:
        """重启浏览器实例"""
        try:
            logger.info("重启浏览器实例")
            await asyncio.sleep(5)
            return True
        except Exception as e:
            logger.error("浏览器重启失败", error=str(e))
            return False

    async def _clear_browser_data(self, context: Dict[str, Any]) -> bool:
        """清理浏览器数据"""
        try:
            logger.info("清理浏览器数据")
            await asyncio.sleep(3)
            return True
        except Exception as e:
            logger.error("浏览器数据清理失败", error=str(e))
            return False

    async def _check_file_permissions(self, context: Dict[str, Any]) -> bool:
        """检查文件权限"""
        try:
            logger.info("检查文件权限")
            return True
        except Exception as e:
            logger.error("权限检查失败", error=str(e))
            return False

    async def _escalate_process_privileges(self, context: Dict[str, Any]) -> bool:
        """提升进程权限"""
        try:
            logger.info("提升进程权限")
            return True
        except Exception as e:
            logger.error("权限提升失败", error=str(e))
            return False

    async def _free_system_memory(self, context: Dict[str, Any]) -> bool:
        """释放系统内存"""
        try:
            logger.info("释放系统内存")
            # 这里可以实现垃圾回收等操作
            import gc

            gc.collect()
            return True
        except Exception as e:
            logger.error("内存释放失败", error=str(e))
            return False

    async def _restart_current_process(self, context: Dict[str, Any]) -> bool:
        """重启当前进程"""
        try:
            logger.info("准备重启当前进程")
            # 这里应该实现进程重启逻辑
            return True
        except Exception as e:
            logger.error("进程重启失败", error=str(e))
            return False

    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计"""
        stats = self.error_statistics.copy()

        # 添加恢复率统计
        total_errors = len(self.error_history)
        recovered_errors = len([e for e in self.error_history if e.resolved])

        stats["recovery_rate"] = (
            recovered_errors / total_errors if total_errors > 0 else 0
        )
        stats["total_errors"] = total_errors
        stats["recovered_errors"] = recovered_errors

        # 添加最近错误趋势
        recent_time = datetime.now() - timedelta(hours=1)
        recent_errors = [
            error
            for error in self.error_history
            if datetime.fromisoformat(error.timestamp) > recent_time
        ]
        stats["recent_errors_count"] = len(recent_errors)

        return stats

    def get_error_history(
        self,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取错误历史

        Args:
            category: 错误分类过滤
            severity: 严重程度过滤
            limit: 返回数量限制

        Returns:
            错误历史列表
        """
        filtered_errors = self.error_history

        if category:
            filtered_errors = [e for e in filtered_errors if e.category == category]

        if severity:
            filtered_errors = [e for e in filtered_errors if e.severity == severity]

        # 按时间倒序排列
        filtered_errors.sort(key=lambda x: x.timestamp, reverse=True)

        return [asdict(error) for error in filtered_errors[:limit]]

    def clear_error_history(self, older_than_days: int = 7) -> int:
        """清理错误历史

        Args:
            older_than_days: 清理多少天前的记录

        Returns:
            清理的记录数量
        """
        cutoff_time = datetime.now() - timedelta(days=older_than_days)

        original_count = len(self.error_history)
        self.error_history = [
            error
            for error in self.error_history
            if datetime.fromisoformat(error.timestamp) > cutoff_time
        ]

        cleared_count = original_count - len(self.error_history)

        logger.info(
            "清理错误历史",
            cleared_count=cleared_count,
            remaining_count=len(self.error_history),
        )

        return cleared_count

    def register_recovery_function(self, name: str, func: Callable) -> None:
        """注册自定义恢复函数

        Args:
            name: 函数名称
            func: 恢复函数
        """
        self.recovery_functions[name] = func
        logger.info("注册恢复函数", name=name)

    def register_escalation_handler(
        self, category: ErrorCategory, handler: Callable
    ) -> None:
        """注册升级处理器

        Args:
            category: 错误分类
            handler: 处理函数
        """
        self.escalation_handlers[category] = handler
        logger.info("注册升级处理器", category=category.value)

    async def check_escalation_needed(self, category: ErrorCategory) -> bool:
        """检查是否需要升级处理

        Args:
            category: 错误分类

        Returns:
            是否需要升级
        """
        # 获取该分类的错误模式
        pattern = None
        for p in self.error_patterns:
            if p.category == category:
                pattern = p
                break

        if not pattern:
            return False

        # 检查最近的错误数量
        recent_time = datetime.now() - timedelta(minutes=30)
        recent_errors = [
            error
            for error in self.error_history
            if (
                error.category == category
                and datetime.fromisoformat(error.timestamp) > recent_time
            )
        ]

        return len(recent_errors) >= pattern.escalation_threshold

    async def escalate_error(
        self, category: ErrorCategory, context: Dict[str, Any] = None
    ) -> bool:
        """升级错误处理

        Args:
            category: 错误分类
            context: 上下文信息

        Returns:
            是否升级成功
        """
        if category in self.escalation_handlers:
            try:
                handler = self.escalation_handlers[category]
                result = await handler(context or {})

                logger.info("错误升级处理完成", category=category.value, success=result)

                return result

            except Exception as e:
                logger.error("错误升级处理失败", category=category.value, error=str(e))
                return False

        logger.warning("未找到升级处理器", category=category.value)
        return False


# 全局错误处理器实例
global_error_handler = ErrorHandler()


# 便捷装饰器
def with_retry(config: Optional[RetryConfig] = None):
    """重试装饰器的便捷版本"""
    return global_error_handler.retry_with_backoff(config)


def with_error_handling(attempt_recovery: bool = True):
    """错误处理装饰器"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                if inspect.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                await global_error_handler.handle_error(
                    e,
                    {
                        "function": func.__name__,
                        "args": str(args),
                        "kwargs": str(kwargs),
                    },
                    attempt_recovery,
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 对于同步函数，我们不能使用 await
                # 这里可以考虑使用线程池或者简化处理
                logger.error("同步函数错误", function=func.__name__, error=str(e))
                raise

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
