"""
性能监控工具 - 监控内存使用、执行时间等性能指标
"""

import gc
import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import psutil

from utils.logger import logger


@dataclass
class PerformanceMetrics:
    """性能指标数据"""

    timestamp: datetime
    memory_usage_mb: float
    cpu_percent: float
    active_threads: int
    gc_collections: Dict[str, int]
    test_execution_time: float = 0.0
    browser_instances: int = 0


@dataclass
class PerformanceStats:
    """性能统计信息"""

    peak_memory_mb: float = 0.0
    average_memory_mb: float = 0.0
    peak_cpu_percent: float = 0.0
    average_cpu_percent: float = 0.0
    total_gc_collections: int = 0
    total_test_time: float = 0.0
    metrics_history: List[PerformanceMetrics] = field(default_factory=list)


class PerformanceMonitor:
    """
    性能监控器

    功能：
    1. 实时监控内存和CPU使用情况
    2. 跟踪垃圾回收统计
    3. 监控浏览器实例数量
    4. 记录测试执行时间
    5. 生成性能报告
    """

    def __init__(
        self,
        monitoring_interval: float = 10.0,
        max_history: int = 100,
        lightweight_mode: bool = True,
    ):
        """
        初始化性能监控器

        Args:
            monitoring_interval: 监控间隔（秒）- 增加到10秒减少开销
            max_history: 最大历史记录数 - 减少到100条减少内存使用
            lightweight_mode: 轻量级模式 - 减少监控项目和频率
        """
        self.monitoring_interval = monitoring_interval
        self.max_history = max_history
        self.lightweight_mode = lightweight_mode

        self.stats = PerformanceStats()
        self.is_monitoring = False
        self._monitor_thread = None
        self._lock = threading.RLock()

        # 获取当前进程
        self.process = psutil.Process()

        # 初始GC统计
        self._initial_gc_stats = self._get_gc_stats()

    def start_monitoring(self):
        """开始性能监控"""
        if self.is_monitoring:
            logger.warning("性能监控已在运行")
            return

        self.is_monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_worker, daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"性能监控已启动，监控间隔: {self.monitoring_interval}秒")

    def stop_monitoring(self):
        """停止性能监控"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            # 减少等待时间，避免阻塞
            self._monitor_thread.join(timeout=1.0)
            if self._monitor_thread.is_alive():
                logger.warning("性能监控线程未能及时停止，但不影响程序退出")
        logger.info("性能监控已停止")

    def _monitor_worker(self):
        """监控工作线程"""
        while self.is_monitoring:
            try:
                self._collect_metrics()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"性能监控错误: {e}")

    def _collect_metrics(self):
        """收集性能指标"""
        try:
            # 内存使用情况
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            # CPU使用率
            cpu_percent = self.process.cpu_percent()

            # 活跃线程数
            active_threads = threading.active_count()

            # GC统计
            gc_stats = self._get_gc_stats()

            # 浏览器实例数（轻量级模式下减少检测频率）
            if self.lightweight_mode and len(self.stats.metrics_history) % 3 != 0:
                # 轻量级模式下，每3次监控才检测一次浏览器实例
                browser_instances = (
                    self.stats.metrics_history[-1].browser_instances
                    if self.stats.metrics_history
                    else 1
                )
            else:
                browser_instances = self._get_browser_instances_count()

            # 创建性能指标
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                memory_usage_mb=memory_mb,
                cpu_percent=cpu_percent,
                active_threads=active_threads,
                gc_collections=gc_stats,
                browser_instances=browser_instances,
            )

            # 更新统计信息
            with self._lock:
                self.stats.metrics_history.append(metrics)

                # 限制历史记录数量
                if len(self.stats.metrics_history) > self.max_history:
                    self.stats.metrics_history.pop(0)

                # 更新峰值和平均值
                self._update_stats(metrics)

        except Exception as e:
            logger.error(f"收集性能指标失败: {e}")

    def _get_gc_stats(self) -> Dict[str, int]:
        """获取垃圾回收统计"""
        try:
            return {f"gen_{i}": gc.get_count()[i] for i in range(len(gc.get_count()))}
        except Exception:
            return {}

    def _get_browser_instances_count(self) -> int:
        """获取浏览器实例数量（简化检测，减少开销）"""
        try:
            # 简化检测逻辑，只检查关键进程
            import psutil

            browser_processes = 0

            # 只检查进程名称，避免读取命令行参数（开销大）
            for proc in psutil.process_iter(["name"]):
                try:
                    proc_name = proc.info.get("name", "").lower()

                    # 只检查明确的浏览器进程名
                    if any(
                        browser in proc_name
                        for browser in ["chrome", "chromium", "firefox", "webkit"]
                    ):
                        browser_processes += 1
                        if browser_processes >= 2:  # 提前退出，减少遍历
                            break

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue

            return min(browser_processes, 2)  # 进一步限制数量
        except Exception:
            return 1  # 默认假设有1个浏览器实例

    def _update_stats(self, metrics: PerformanceMetrics):
        """更新统计信息"""
        # 更新峰值
        self.stats.peak_memory_mb = max(
            self.stats.peak_memory_mb, metrics.memory_usage_mb
        )
        self.stats.peak_cpu_percent = max(
            self.stats.peak_cpu_percent, metrics.cpu_percent
        )

        # 计算平均值
        if self.stats.metrics_history:
            memory_values = [m.memory_usage_mb for m in self.stats.metrics_history]
            cpu_values = [m.cpu_percent for m in self.stats.metrics_history]

            self.stats.average_memory_mb = sum(memory_values) / len(memory_values)
            self.stats.average_cpu_percent = sum(cpu_values) / len(cpu_values)

    def record_test_execution_time(self, execution_time: float):
        """记录测试执行时间"""
        with self._lock:
            self.stats.total_test_time += execution_time

    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """获取当前性能指标"""
        with self._lock:
            if self.stats.metrics_history:
                return self.stats.metrics_history[-1]
            return None

    def get_stats(self) -> PerformanceStats:
        """获取性能统计信息"""
        with self._lock:
            return self.stats

    def generate_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        with self._lock:
            current_metrics = self.get_current_metrics()

            report = {
                "summary": {
                    "monitoring_duration_minutes": len(self.stats.metrics_history)
                    * self.monitoring_interval
                    / 60,
                    "peak_memory_mb": round(self.stats.peak_memory_mb, 2),
                    "average_memory_mb": round(self.stats.average_memory_mb, 2),
                    "peak_cpu_percent": round(self.stats.peak_cpu_percent, 2),
                    "average_cpu_percent": round(self.stats.average_cpu_percent, 2),
                    "total_test_time_seconds": round(self.stats.total_test_time, 2),
                    "current_browser_instances": (
                        current_metrics.browser_instances if current_metrics else 0
                    ),
                },
                "recommendations": self._generate_recommendations(),
                "metrics_count": len(self.stats.metrics_history),
            }

            return report

    def _generate_recommendations(self) -> List[str]:
        """生成性能优化建议"""
        recommendations = []

        # 内存使用建议
        if self.stats.peak_memory_mb > 500:
            recommendations.append("内存使用峰值较高，建议检查内存泄漏或优化数据结构")

        if self.stats.average_memory_mb > 300:
            recommendations.append("平均内存使用较高，建议优化数据结构或减少数据保留")

        # CPU使用建议
        if self.stats.peak_cpu_percent > 80:
            recommendations.append("CPU使用峰值较高，建议优化算法或减少并发操作")

        if not recommendations:
            recommendations.append("性能表现良好，无特殊优化建议")

        return recommendations

    def save_report(self, file_path: str = "reports/performance_report.json"):
        """保存性能报告到文件"""
        report = self.generate_report()

        # 确保目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"性能报告已保存到: {file_path}")

    def reset_stats(self):
        """重置统计信息"""
        with self._lock:
            self.stats = PerformanceStats()
            self._initial_gc_stats = self._get_gc_stats()
        logger.debug("性能统计信息已重置")

    def force_gc(self):
        """强制垃圾回收"""
        before_memory = self.process.memory_info().rss / 1024 / 1024

        # 执行垃圾回收
        collected = gc.collect()

        after_memory = self.process.memory_info().rss / 1024 / 1024
        freed_memory = before_memory - after_memory

        logger.info(
            f"强制垃圾回收完成: 回收对象 {collected} 个, 释放内存 {freed_memory:.2f}MB"
        )

        return {
            "collected_objects": collected,
            "freed_memory_mb": round(freed_memory, 2),
            "before_memory_mb": round(before_memory, 2),
            "after_memory_mb": round(after_memory, 2),
        }


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()
