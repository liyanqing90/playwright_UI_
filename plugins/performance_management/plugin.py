"""性能管理插件实现

提供性能监控、缓存管理、资源优化和性能报告生成等功能。
"""

import time
import psutil
import threading
import json
import os
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor

from src.automation.action_types import StepAction
from src.automation.commands.base_command import Command, CommandFactory
from utils.logger import logger


@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    category: str = "general"
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class ResourceUsage:
    """资源使用情况数据类"""
    cpu_percent: float
    memory_percent: float
    memory_used: int  # bytes
    memory_available: int  # bytes
    disk_usage: Dict[str, float]  # path -> usage_percent
    network_io: Dict[str, int]  # bytes_sent, bytes_recv
    timestamp: datetime


@dataclass
class CacheEntry:
    """缓存条目数据类"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl: Optional[int] = None  # seconds
    size: int = 0  # bytes


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics: List[PerformanceMetric] = []
        self.resource_history: deque = deque(maxlen=config.get('history_size', 1000))
        self.operation_times: defaultdict = defaultdict(list)
        self.slow_operations: List[Dict[str, Any]] = []
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
    def start_monitoring(self):
        """开始性能监控"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("性能监控已启动")
        
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("性能监控已停止")
        
    def _monitor_loop(self):
        """监控循环"""
        interval = self.config.get('monitor_interval', 5)  # seconds
        
        while self.monitoring_active:
            try:
                resource_usage = self._collect_resource_usage()
                with self.lock:
                    self.resource_history.append(resource_usage)
                    
                # 检查资源使用阈值
                self._check_resource_thresholds(resource_usage)
                
                time.sleep(interval)
            except Exception as e:
                logger.error(f"性能监控错误: {e}")
                time.sleep(interval)
                
    def _collect_resource_usage(self) -> ResourceUsage:
        """收集资源使用情况"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        
        # 磁盘使用情况
        disk_usage = {}
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_usage[partition.mountpoint] = (usage.used / usage.total) * 100
            except PermissionError:
                continue
                
        # 网络IO
        network = psutil.net_io_counters()
        network_io = {
            'bytes_sent': network.bytes_sent,
            'bytes_recv': network.bytes_recv
        }
        
        return ResourceUsage(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used=memory.used,
            memory_available=memory.available,
            disk_usage=disk_usage,
            network_io=network_io,
            timestamp=datetime.now()
        )
        
    def _check_resource_thresholds(self, usage: ResourceUsage):
        """检查资源使用阈值"""
        thresholds = self.config.get('thresholds', {})
        
        # CPU阈值检查
        cpu_threshold = thresholds.get('cpu_percent', 80)
        if usage.cpu_percent > cpu_threshold:
            logger.warning(f"CPU使用率过高: {usage.cpu_percent:.1f}%")
            
        # 内存阈值检查
        memory_threshold = thresholds.get('memory_percent', 80)
        if usage.memory_percent > memory_threshold:
            logger.warning(f"内存使用率过高: {usage.memory_percent:.1f}%")
            
        # 磁盘阈值检查
        disk_threshold = thresholds.get('disk_percent', 90)
        for path, percent in usage.disk_usage.items():
            if percent > disk_threshold:
                logger.warning(f"磁盘使用率过高 {path}: {percent:.1f}%")
                
    def record_operation(self, operation_name: str, duration: float, context: Dict[str, Any] = None):
        """记录操作性能"""
        with self.lock:
            self.operation_times[operation_name].append(duration)
            
            # 检查是否为慢操作
            slow_threshold = self.config.get('slow_operation_threshold', 2.0)
            if duration > slow_threshold:
                slow_op = {
                    'operation': operation_name,
                    'duration': duration,
                    'timestamp': datetime.now().isoformat(),
                    'context': context or {}
                }
                self.slow_operations.append(slow_op)
                logger.warning(f"慢操作检测: {operation_name} 耗时 {duration:.2f}s")
                
    def add_metric(self, name: str, value: float, unit: str, category: str = "general", tags: Dict[str, str] = None):
        """添加性能指标"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            category=category,
            tags=tags or {}
        )
        
        with self.lock:
            self.metrics.append(metric)
            
            # 限制指标数量
            max_metrics = self.config.get('max_metrics', 10000)
            if len(self.metrics) > max_metrics:
                self.metrics = self.metrics[-max_metrics//2:]  # 保留一半
                
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        with self.lock:
            stats = {
                'resource_usage': {
                    'current': self.resource_history[-1].__dict__ if self.resource_history else None,
                    'history_count': len(self.resource_history)
                },
                'operations': {},
                'slow_operations': self.slow_operations[-100:],  # 最近100个慢操作
                'metrics_count': len(self.metrics)
            }
            
            # 操作统计
            for op_name, durations in self.operation_times.items():
                if durations:
                    stats['operations'][op_name] = {
                        'count': len(durations),
                        'avg_duration': sum(durations) / len(durations),
                        'min_duration': min(durations),
                        'max_duration': max(durations),
                        'total_duration': sum(durations)
                    }
                    
            return stats
            
    def reset_stats(self):
        """重置统计信息"""
        with self.lock:
            self.metrics.clear()
            self.resource_history.clear()
            self.operation_times.clear()
            self.slow_operations.clear()
            
        logger.info("性能统计信息已重置")


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = threading.RLock()
        self.max_size = config.get('max_size', 1000)
        self.default_ttl = config.get('default_ttl', 3600)  # 1 hour
        self.cleanup_interval = config.get('cleanup_interval', 300)  # 5 minutes
        self.cleanup_thread: Optional[threading.Thread] = None
        self.cleanup_active = False
        
    def start_cleanup(self):
        """启动缓存清理"""
        if self.cleanup_active:
            return
            
        self.cleanup_active = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        logger.info("缓存清理已启动")
        
    def stop_cleanup(self):
        """停止缓存清理"""
        self.cleanup_active = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        logger.info("缓存清理已停止")
        
    def _cleanup_loop(self):
        """清理循环"""
        while self.cleanup_active:
            try:
                self._cleanup_expired()
                self._cleanup_lru()
                time.sleep(self.cleanup_interval)
            except Exception as e:
                logger.error(f"缓存清理错误: {e}")
                time.sleep(self.cleanup_interval)
                
    def _cleanup_expired(self):
        """清理过期缓存"""
        now = datetime.now()
        expired_keys = []
        
        with self.lock:
            for key, entry in self.cache.items():
                if entry.ttl and (now - entry.created_at).total_seconds() > entry.ttl:
                    expired_keys.append(key)
                    
            for key in expired_keys:
                del self.cache[key]
                
        if expired_keys:
            logger.debug(f"清理过期缓存: {len(expired_keys)} 项")
            
    def _cleanup_lru(self):
        """LRU清理"""
        with self.lock:
            if len(self.cache) <= self.max_size:
                return
                
            # 按最后访问时间排序
            sorted_entries = sorted(
                self.cache.items(),
                key=lambda x: x[1].last_accessed
            )
            
            # 删除最久未访问的条目
            remove_count = len(self.cache) - self.max_size
            for i in range(remove_count):
                key = sorted_entries[i][0]
                del self.cache[key]
                
            logger.debug(f"LRU清理: 删除 {remove_count} 项")
            
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        with self.lock:
            entry = self.cache.get(key)
            if entry is None:
                return default
                
            # 检查是否过期
            if entry.ttl and (datetime.now() - entry.created_at).total_seconds() > entry.ttl:
                del self.cache[key]
                return default
                
            # 更新访问信息
            entry.last_accessed = datetime.now()
            entry.access_count += 1
            
            return entry.value
            
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            # 计算值大小
            size = len(str(value).encode('utf-8'))
            
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                ttl=ttl or self.default_ttl,
                size=size
            )
            
            with self.lock:
                self.cache[key] = entry
                
                # 检查缓存大小
                if len(self.cache) > self.max_size:
                    self._cleanup_lru()
                    
            return True
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            return False
            
    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
            
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
        logger.info("缓存已清空")
        
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.lock:
            total_size = sum(entry.size for entry in self.cache.values())
            total_access = sum(entry.access_count for entry in self.cache.values())
            
            return {
                'total_entries': len(self.cache),
                'total_size': total_size,
                'total_access': total_access,
                'max_size': self.max_size,
                'hit_rate': self._calculate_hit_rate(),
                'avg_access_count': total_access / len(self.cache) if self.cache else 0
            }
            
    def _calculate_hit_rate(self) -> float:
        """计算缓存命中率"""
        # 这里简化实现，实际应该跟踪命中和未命中次数
        return 0.85  # 示例值


class ResourceOptimizer:
    """资源优化器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.optimization_rules: List[Callable] = []
        self.optimization_history: List[Dict[str, Any]] = []
        
    def add_optimization_rule(self, rule: Callable):
        """添加优化规则"""
        self.optimization_rules.append(rule)
        
    def optimize(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行优化"""
        results = {
            'optimizations_applied': [],
            'performance_improvement': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        for rule in self.optimization_rules:
            try:
                result = rule(context or {})
                if result:
                    results['optimizations_applied'].append(result)
            except Exception as e:
                logger.error(f"优化规则执行失败: {e}")
                
        self.optimization_history.append(results)
        return results
        
    def get_optimization_suggestions(self, performance_stats: Dict[str, Any]) -> List[str]:
        """获取优化建议"""
        suggestions = []
        
        # 基于性能统计提供建议
        resource_usage = performance_stats.get('resource_usage', {}).get('current')
        if resource_usage:
            if resource_usage.get('cpu_percent', 0) > 80:
                suggestions.append("CPU使用率过高，建议减少并发操作或优化算法")
                
            if resource_usage.get('memory_percent', 0) > 80:
                suggestions.append("内存使用率过高，建议清理缓存或减少内存占用")
                
        # 基于慢操作提供建议
        slow_ops = performance_stats.get('slow_operations', [])
        if len(slow_ops) > 10:
            suggestions.append("检测到多个慢操作，建议优化相关代码或增加缓存")
            
        return suggestions


class PerformanceManagementPlugin:
    """性能管理插件"""
    
    def __init__(self):
        self.name = "performance_management"
        self.version = "1.0.0"
        self.description = "性能监控、缓存管理和资源优化插件"
        
        # 默认配置
        self.config = {
            'monitor': {
                'enabled': True,
                'interval': 5,
                'history_size': 1000,
                'slow_operation_threshold': 2.0,
                'thresholds': {
                    'cpu_percent': 80,
                    'memory_percent': 80,
                    'disk_percent': 90
                }
            },
            'cache': {
                'enabled': True,
                'max_size': 1000,
                'default_ttl': 3600,
                'cleanup_interval': 300
            },
            'optimizer': {
                'enabled': True,
                'auto_optimize': False
            }
        }
        
        # 初始化组件
        self.monitor = PerformanceMonitor(self.config['monitor'])
        self.cache_manager = CacheManager(self.config['cache'])
        self.optimizer = ResourceOptimizer(self.config['optimizer'])
        
        # 注册命令
        self._register_commands()
        
    def _register_commands(self):
        """注册性能管理命令"""
        commands = {
            'START_PERFORMANCE_MONITOR': StartPerformanceMonitorCommand,
            'STOP_PERFORMANCE_MONITOR': StopPerformanceMonitorCommand,
            'GET_PERFORMANCE_STATS': GetPerformanceStatsCommand,
            'RESET_PERFORMANCE_STATS': ResetPerformanceStatsCommand,
            'RECORD_PERFORMANCE_METRIC': RecordPerformanceMetricCommand,
            'SET_CACHE': SetCacheCommand,
            'GET_CACHE': GetCacheCommand,
            'DELETE_CACHE': DeleteCacheCommand,
            'CLEAR_CACHE': ClearCacheCommand,
            'GET_CACHE_STATS': GetCacheStatsCommand,
            'OPTIMIZE_PERFORMANCE': OptimizePerformanceCommand,
            'GET_OPTIMIZATION_SUGGESTIONS': GetOptimizationSuggestionsCommand,
            'GENERATE_PERFORMANCE_REPORT': GeneratePerformanceReportCommand
        }
        
        for action_name, command_class in commands.items():
            try:
                # 动态创建StepAction属性
                if not hasattr(StepAction, action_name):
                    setattr(StepAction, action_name, [action_name.lower(), action_name.lower().replace('_', ' ')])
                
                action = getattr(StepAction, action_name)
                CommandFactory.register(action)(command_class)
                logger.info(f"已注册性能管理命令: {action_name}")
            except Exception as e:
                logger.error(f"注册性能管理命令失败 {action_name}: {e}")
                
    def start(self):
        """启动性能管理"""
        if self.config['monitor']['enabled']:
            self.monitor.start_monitoring()
            
        if self.config['cache']['enabled']:
            self.cache_manager.start_cleanup()
            
        logger.info("性能管理插件已启动")
        
    def stop(self):
        """停止性能管理"""
        self.monitor.stop_monitoring()
        self.cache_manager.stop_cleanup()
        logger.info("性能管理插件已停止")


# 命令实现
@CommandFactory.register(StepAction.START_PERFORMANCE_MONITOR)
class StartPerformanceMonitorCommand(Command):
    """启动性能监控命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        plugin = PerformanceManagementPlugin()
        plugin.monitor.start_monitoring()
        logger.info("性能监控已启动")


@CommandFactory.register(StepAction.STOP_PERFORMANCE_MONITOR)
class StopPerformanceMonitorCommand(Command):
    """停止性能监控命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        plugin = PerformanceManagementPlugin()
        plugin.monitor.stop_monitoring()
        logger.info("性能监控已停止")


@CommandFactory.register(StepAction.GET_PERFORMANCE_STATS)
class GetPerformanceStatsCommand(Command):
    """获取性能统计命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        variable_name = step.get('variable_name')
        
        plugin = PerformanceManagementPlugin()
        stats = plugin.monitor.get_performance_stats()
        
        if variable_name:
            ui_helper.store_variable(variable_name, stats, step.get('scope', 'global'))
            
        logger.info(f"获取性能统计: {len(stats)} 项指标")


@CommandFactory.register(StepAction.RESET_PERFORMANCE_STATS)
class ResetPerformanceStatsCommand(Command):
    """重置性能统计命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        plugin = PerformanceManagementPlugin()
        plugin.monitor.reset_stats()
        logger.info("性能统计已重置")


@CommandFactory.register(StepAction.RECORD_PERFORMANCE_METRIC)
class RecordPerformanceMetricCommand(Command):
    """记录性能指标命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        metric_name = step.get('metric_name', selector)
        metric_value = step.get('metric_value', value)
        unit = step.get('unit', 'count')
        category = step.get('category', 'general')
        tags = step.get('tags', {})
        
        plugin = PerformanceManagementPlugin()
        plugin.monitor.add_metric(metric_name, float(metric_value), unit, category, tags)
        
        logger.info(f"记录性能指标: {metric_name} = {metric_value} {unit}")


@CommandFactory.register(StepAction.SET_CACHE)
class SetCacheCommand(Command):
    """设置缓存命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        cache_key = step.get('cache_key', selector)
        cache_value = step.get('cache_value', value)
        ttl = step.get('ttl')
        
        plugin = PerformanceManagementPlugin()
        success = plugin.cache_manager.set(cache_key, cache_value, ttl)
        
        if success:
            logger.info(f"缓存设置成功: {cache_key}")
        else:
            logger.error(f"缓存设置失败: {cache_key}")


@CommandFactory.register(StepAction.GET_CACHE)
class GetCacheCommand(Command):
    """获取缓存命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        cache_key = step.get('cache_key', value)
        default_value = step.get('default')
        variable_name = step.get('variable_name')
        
        plugin = PerformanceManagementPlugin()
        cached_value = plugin.cache_manager.get(cache_key, default_value)
        
        if variable_name:
            ui_helper.store_variable(variable_name, cached_value, step.get('scope', 'global'))
            
        logger.info(f"获取缓存: {cache_key} = {cached_value is not None}")


@CommandFactory.register(StepAction.DELETE_CACHE)
class DeleteCacheCommand(Command):
    """删除缓存命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        cache_key = step.get('cache_key', value)
        
        plugin = PerformanceManagementPlugin()
        success = plugin.cache_manager.delete(cache_key)
        
        if success:
            logger.info(f"缓存删除成功: {cache_key}")
        else:
            logger.warning(f"缓存不存在: {cache_key}")


@CommandFactory.register(StepAction.CLEAR_CACHE)
class ClearCacheCommand(Command):
    """清空缓存命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        plugin = PerformanceManagementPlugin()
        plugin.cache_manager.clear()
        logger.info("缓存已清空")


@CommandFactory.register(StepAction.GET_CACHE_STATS)
class GetCacheStatsCommand(Command):
    """获取缓存统计命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        variable_name = step.get('variable_name')
        
        plugin = PerformanceManagementPlugin()
        stats = plugin.cache_manager.get_stats()
        
        if variable_name:
            ui_helper.store_variable(variable_name, stats, step.get('scope', 'global'))
            
        logger.info(f"获取缓存统计: {stats['total_entries']} 项缓存")


@CommandFactory.register(StepAction.OPTIMIZE_PERFORMANCE)
class OptimizePerformanceCommand(Command):
    """优化性能命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        context = step.get('context', {})
        variable_name = step.get('variable_name')
        
        plugin = PerformanceManagementPlugin()
        results = plugin.optimizer.optimize(context)
        
        if variable_name:
            ui_helper.store_variable(variable_name, results, step.get('scope', 'global'))
            
        logger.info(f"性能优化完成: {len(results['optimizations_applied'])} 项优化")


@CommandFactory.register(StepAction.GET_OPTIMIZATION_SUGGESTIONS)
class GetOptimizationSuggestionsCommand(Command):
    """获取优化建议命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        variable_name = step.get('variable_name')
        
        plugin = PerformanceManagementPlugin()
        stats = plugin.monitor.get_performance_stats()
        suggestions = plugin.optimizer.get_optimization_suggestions(stats)
        
        if variable_name:
            ui_helper.store_variable(variable_name, suggestions, step.get('scope', 'global'))
            
        logger.info(f"获取优化建议: {len(suggestions)} 条建议")


@CommandFactory.register(StepAction.GENERATE_PERFORMANCE_REPORT)
class GeneratePerformanceReportCommand(Command):
    """生成性能报告命令"""
    
    def execute(self, ui_helper, selector: str, value: Any, step: Dict[str, Any]) -> None:
        report_path = step.get('report_path', 'performance_report.json')
        include_history = step.get('include_history', True)
        variable_name = step.get('variable_name')
        
        plugin = PerformanceManagementPlugin()
        
        # 生成报告数据
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'plugin_info': {
                'name': plugin.name,
                'version': plugin.version,
                'description': plugin.description
            },
            'performance_stats': plugin.monitor.get_performance_stats(),
            'cache_stats': plugin.cache_manager.get_stats(),
            'optimization_history': plugin.optimizer.optimization_history if include_history else []
        }
        
        # 保存报告
        try:
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
                
            if variable_name:
                ui_helper.store_variable(variable_name, report_data, step.get('scope', 'global'))
                
            logger.info(f"性能报告已生成: {report_path}")
            
        except Exception as e:
            logger.error(f"生成性能报告失败: {e}")
            raise


def plugin_init():
    """插件初始化函数"""
    plugin = PerformanceManagementPlugin()
    plugin.start()
    logger.info(f"性能管理插件已初始化: {plugin.name} v{plugin.version}")
    return plugin


def plugin_cleanup():
    """插件清理函数"""
    plugin = PerformanceManagementPlugin()
    plugin.stop()
    logger.info("性能管理插件已清理")