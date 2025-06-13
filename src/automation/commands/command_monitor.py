"""命令性能监控器"""

import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


@dataclass
class CommandMetrics:
    """命令执行指标"""
    command_name: str
    execution_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    error_count: int = 0
    last_execution: Optional[float] = None
    recent_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def update(self, execution_time: float, success: bool = True):
        """更新指标"""
        self.execution_count += 1
        self.total_time += execution_time
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.avg_time = self.total_time / self.execution_count
        self.last_execution = time.time()
        self.recent_times.append(execution_time)
        
        if not success:
            self.error_count += 1
    
    def get_recent_avg(self, count: int = 10) -> float:
        """获取最近N次执行的平均时间"""
        if not self.recent_times:
            return 0.0
        recent = list(self.recent_times)[-count:]
        return sum(recent) / len(recent)
    
    def get_error_rate(self) -> float:
        """获取错误率"""
        if self.execution_count == 0:
            return 0.0
        return self.error_count / self.execution_count


class CommandMonitor:
    """命令监控器"""
    
    def __init__(self):
        self.metrics: Dict[str, CommandMetrics] = defaultdict(lambda: CommandMetrics(""))
        self.enabled = True
        self.slow_threshold = 1.0  # 慢命令阈值（秒）
        self.error_threshold = 0.1  # 错误率阈值
        self.listeners: List[Callable] = []
        self._lock = threading.Lock()
    
    def enable(self):
        """启用监控"""
        self.enabled = True
        logger.info("Command monitoring enabled")
    
    def disable(self):
        """禁用监控"""
        self.enabled = False
        logger.info("Command monitoring disabled")
    
    def set_slow_threshold(self, threshold: float):
        """设置慢命令阈值"""
        self.slow_threshold = threshold
        logger.info(f"Slow command threshold set to {threshold}s")
    
    def set_error_threshold(self, threshold: float):
        """设置错误率阈值"""
        self.error_threshold = threshold
        logger.info(f"Error rate threshold set to {threshold}")
    
    def add_listener(self, listener: Callable[[str, CommandMetrics], None]):
        """添加监控事件监听器"""
        self.listeners.append(listener)
    
    def remove_listener(self, listener: Callable):
        """移除监控事件监听器"""
        if listener in self.listeners:
            self.listeners.remove(listener)
    
    @contextmanager
    def monitor_command(self, command_name: str):
        """监控命令执行的上下文管理器"""
        if not self.enabled:
            yield
            return
        
        start_time = time.time()
        success = True
        
        try:
            yield
        except Exception as e:
            success = False
            raise
        finally:
            execution_time = time.time() - start_time
            self._record_execution(command_name, execution_time, success)
    
    def _record_execution(self, command_name: str, execution_time: float, success: bool):
        """记录命令执行"""
        with self._lock:
            if command_name not in self.metrics:
                self.metrics[command_name] = CommandMetrics(command_name)
            
            metrics = self.metrics[command_name]
            metrics.update(execution_time, success)
            
            # 检查是否需要触发警告
            self._check_alerts(command_name, metrics, execution_time, success)
            
            # 通知监听器
            for listener in self.listeners:
                try:
                    listener(command_name, metrics)
                except Exception as e:
                    logger.error(f"Error in monitor listener: {e}")
    
    def _check_alerts(self, command_name: str, metrics: CommandMetrics, 
                     execution_time: float, success: bool):
        """检查并触发警告"""
        # 慢命令警告
        if execution_time > self.slow_threshold:
            logger.warning(
                f"Slow command detected: {command_name} took {execution_time:.2f}s "
                f"(threshold: {self.slow_threshold}s)"
            )
        
        # 错误率警告
        if not success and metrics.get_error_rate() > self.error_threshold:
            logger.warning(
                f"High error rate for command {command_name}: "
                f"{metrics.get_error_rate():.2%} (threshold: {self.error_threshold:.2%})"
            )
    
    def get_metrics(self, command_name: str = None) -> Dict[str, CommandMetrics]:
        """获取指标"""
        with self._lock:
            if command_name:
                return {command_name: self.metrics.get(command_name, CommandMetrics(command_name))}
            return dict(self.metrics)
    
    def get_slow_commands(self, threshold: float = None) -> List[CommandMetrics]:
        """获取慢命令列表"""
        threshold = threshold or self.slow_threshold
        with self._lock:
            return [
                metrics for metrics in self.metrics.values()
                if metrics.avg_time > threshold
            ]
    
    def get_error_prone_commands(self, threshold: float = None) -> List[CommandMetrics]:
        """获取高错误率命令列表"""
        threshold = threshold or self.error_threshold
        with self._lock:
            return [
                metrics for metrics in self.metrics.values()
                if metrics.get_error_rate() > threshold
            ]
    
    def get_top_commands(self, limit: int = 10, sort_by: str = 'total_time') -> List[CommandMetrics]:
        """获取排行榜"""
        with self._lock:
            commands = list(self.metrics.values())
            
            if sort_by == 'total_time':
                commands.sort(key=lambda x: x.total_time, reverse=True)
            elif sort_by == 'avg_time':
                commands.sort(key=lambda x: x.avg_time, reverse=True)
            elif sort_by == 'execution_count':
                commands.sort(key=lambda x: x.execution_count, reverse=True)
            elif sort_by == 'error_rate':
                commands.sort(key=lambda x: x.get_error_rate(), reverse=True)
            
            return commands[:limit]
    
    def reset_metrics(self, command_name: str = None):
        """重置指标"""
        with self._lock:
            if command_name:
                if command_name in self.metrics:
                    del self.metrics[command_name]
                    logger.info(f"Reset metrics for command: {command_name}")
            else:
                self.metrics.clear()
                logger.info("Reset all command metrics")
    
    def export_metrics(self) -> Dict[str, Dict[str, Any]]:
        """导出指标数据"""
        with self._lock:
            result = {}
            for name, metrics in self.metrics.items():
                result[name] = {
                    'command_name': metrics.command_name,
                    'execution_count': metrics.execution_count,
                    'total_time': metrics.total_time,
                    'min_time': metrics.min_time if metrics.min_time != float('inf') else 0,
                    'max_time': metrics.max_time,
                    'avg_time': metrics.avg_time,
                    'error_count': metrics.error_count,
                    'error_rate': metrics.get_error_rate(),
                    'last_execution': metrics.last_execution,
                    'recent_avg_10': metrics.get_recent_avg(10),
                    'recent_avg_50': metrics.get_recent_avg(50)
                }
            return result
    
    def generate_report(self) -> str:
        """生成监控报告"""
        with self._lock:
            if not self.metrics:
                return "No command metrics available."
            
            lines = ["\n=== Command Performance Report ==="]
            lines.append(f"Total commands monitored: {len(self.metrics)}")
            lines.append("")
            
            # 总体统计
            total_executions = sum(m.execution_count for m in self.metrics.values())
            total_time = sum(m.total_time for m in self.metrics.values())
            total_errors = sum(m.error_count for m in self.metrics.values())
            
            lines.append("=== Overall Statistics ===")
            lines.append(f"Total executions: {total_executions}")
            lines.append(f"Total time: {total_time:.2f}s")
            lines.append(f"Total errors: {total_errors}")
            lines.append(f"Overall error rate: {total_errors/total_executions:.2%}" if total_executions > 0 else "Overall error rate: 0%")
            lines.append("")
            
            # 慢命令
            slow_commands = self.get_slow_commands()
            if slow_commands:
                lines.append("=== Slow Commands ===")
                for cmd in slow_commands[:5]:
                    lines.append(f"{cmd.command_name}: {cmd.avg_time:.2f}s avg, {cmd.execution_count} executions")
                lines.append("")
            
            # 高错误率命令
            error_commands = self.get_error_prone_commands()
            if error_commands:
                lines.append("=== High Error Rate Commands ===")
                for cmd in error_commands[:5]:
                    lines.append(f"{cmd.command_name}: {cmd.get_error_rate():.2%} error rate, {cmd.error_count}/{cmd.execution_count} errors")
                lines.append("")
            
            # 最常用命令
            top_commands = self.get_top_commands(5, 'execution_count')
            lines.append("=== Most Used Commands ===")
            for cmd in top_commands:
                lines.append(f"{cmd.command_name}: {cmd.execution_count} executions, {cmd.avg_time:.2f}s avg")
            
            return "\n".join(lines)


# 全局命令监控器实例
command_monitor = CommandMonitor()


# 监控装饰器
def monitor_command(command_name: str = None):
    """命令监控装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            name = command_name or func.__name__
            with command_monitor.monitor_command(name):
                return func(*args, **kwargs)
        return wrapper
    return decorator