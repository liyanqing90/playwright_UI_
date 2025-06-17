import os
import time
from typing import Dict, Any, Optional

import yaml

from utils.logger import logger


class PerformanceManager:
    """性能优化管理器"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config",
            "performance_optimization.yaml",
        )
        self.config = self._load_config()
        self._stats = {
            "total_operations": 0,
            "slow_operations": 0,
            "start_time": time.time(),
        }

    def _load_config(self) -> Dict[str, Any]:
        """加载性能配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                logger.info(f"已加载性能配置: {self.config_path}")
                return config
            else:
                logger.warning(f"性能配置文件不存在: {self.config_path}，使用默认配置")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"加载性能配置失败: {e}，使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            # 元素缓存配置已移除
            "screenshot": {
                "max_count": 50,
                "interval": 1,
                "smart_mode": True,
                "quality": 80,
            },
            "page_load": {
                "disable_images": False,
                "disable_css": False,
                "disable_fonts": False,
                "timeout": 30000,
            },
            "element_wait": {
                "default_timeout": 10000,
                "quick_timeout": 1000,
                "retry_count": 3,
                "retry_interval": 500,
            },
            "monitoring": {
                "enabled": True,
                "log_level": "INFO",
                "slow_threshold": 2.0,
                "memory_check_interval": 30,
            },
            "concurrency": {
                "max_concurrent_locators": 10,
                "batch_size": 20,
                "async_enabled": False,
            },
            "debug": {
                "verbose_logging": False,
                "log_cache_hits": True,
                "log_performance_stats": True,
            },
        }

    def get_config(self, section: str, key: str = None, default=None):
        """获取配置值"""
        try:
            section_config = self.config.get(section, {})
            if key is None:
                return section_config
            return section_config.get(key, default)
        except Exception:
            return default

    def get_max_screenshots(self) -> int:
        """获取最大截图数量"""
        return self.get_config("screenshot", "max_count", 50)

    def get_screenshot_interval(self) -> float:
        """获取截图间隔"""
        return self.get_config("screenshot", "interval", 1.0)

    def get_default_timeout(self) -> int:
        """获取默认超时时间"""
        return self.get_config("element_wait", "default_timeout", 10000)

    def get_slow_threshold(self) -> float:
        """获取慢操作阈值"""
        return self.get_config("monitoring", "slow_threshold", 2.0)

    def is_monitoring_enabled(self) -> bool:
        """检查性能监控是否启用"""
        return self.get_config("monitoring", "enabled", True)

    def should_log_performance_stats(self) -> bool:
        """是否记录性能统计"""
        return self.get_config("debug", "log_performance_stats", True)

    def record_operation(self, duration: float, operation_name: str = ""):
        """记录操作"""
        self._stats["total_operations"] += 1

        if duration > self.get_slow_threshold():
            self._stats["slow_operations"] += 1
            if self.is_monitoring_enabled():
                logger.warning(f"慢操作检测: {operation_name} 耗时 {duration:.3f}s")

        if self.should_log_performance_stats():
            logger.debug(f"操作完成: {operation_name} 耗时 {duration:.3f}s")

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        runtime = time.time() - self._stats["start_time"]

        stats = {
            "runtime_seconds": runtime,
            "total_operations": self._stats["total_operations"],
            "slow_operations": self._stats["slow_operations"],
            "operations_per_second": (
                self._stats["total_operations"] / runtime if runtime > 0 else 0
            ),
            "slow_operation_rate": (
                (self._stats["slow_operations"] / self._stats["total_operations"] * 100)
                if self._stats["total_operations"] > 0
                else 0
            ),
        }

        if self.should_log_performance_stats():
            logger.info(f"性能统计: {stats}")

        return stats

    def reset_stats(self):
        """重置统计数据"""
        self._stats = {
            "total_operations": 0,
            "slow_operations": 0,
            "start_time": time.time(),
        }
        logger.info("性能统计已重置")

    def optimize_for_environment(self, env_type: str = "test"):
        """根据环境类型优化配置"""
        if env_type == "ci":
            # CI环境优化：禁用截图，减少缓存
            self.config["screenshot"]["max_count"] = 10
            self.config["element_cache"]["timeout"] = 10
            self.config["page_load"]["disable_images"] = True
            logger.info("已应用CI环境优化配置")

        elif env_type == "debug":
            # 调试环境：启用详细日志
            self.config["debug"]["verbose_logging"] = True
            self.config["debug"]["log_cache_hits"] = True
            self.config["debug"]["log_performance_stats"] = True
            logger.info("已应用调试环境优化配置")

        elif env_type == "production":
            # 生产环境：最大化性能
            self.config["element_cache"]["timeout"] = 60
            self.config["screenshot"]["smart_mode"] = True
            self.config["page_load"]["disable_images"] = False
            logger.info("已应用生产环境优化配置")


# 全局性能管理器实例
performance_manager = PerformanceManager()
