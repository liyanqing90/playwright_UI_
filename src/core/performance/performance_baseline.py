"""性能基线管理模块

提供性能基线的定义、存储、比较和报告功能。
支持多种性能指标的基线管理和自动化性能回归检测。
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import structlog

logger = structlog.get_logger(__name__)

class MetricType(Enum):
    """性能指标类型"""
    RESPONSE_TIME = "response_time"
    LOAD_TIME = "load_time"
    RENDER_TIME = "render_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    NETWORK_TIME = "network_time"
    DOM_READY = "dom_ready"
    FIRST_PAINT = "first_paint"
    FIRST_CONTENTFUL_PAINT = "first_contentful_paint"
    LARGEST_CONTENTFUL_PAINT = "largest_contentful_paint"
    CUMULATIVE_LAYOUT_SHIFT = "cumulative_layout_shift"
    FIRST_INPUT_DELAY = "first_input_delay"

class ComparisonResult(Enum):
    """性能比较结果"""
    BETTER = "better"
    WORSE = "worse"
    SIMILAR = "similar"
    NO_BASELINE = "no_baseline"

@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceMetric':
        """从字典创建实例"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class BaselineConfig:
    """基线配置"""
    tolerance_percentage: float = 10.0  # 容忍度百分比
    min_samples: int = 5  # 最小样本数
    max_samples: int = 100  # 最大样本数
    outlier_threshold: float = 2.0  # 异常值阈值（标准差倍数）
    auto_update: bool = True  # 是否自动更新基线
    retention_days: int = 30  # 数据保留天数

class PerformanceBaseline:
    """性能基线管理器
    
    负责管理性能基线数据，包括：
    - 基线数据的存储和加载
    - 性能指标的比较和分析
    - 基线的自动更新
    - 性能报告生成
    """
    
    def __init__(self, 
                 baseline_file: Optional[Union[str, Path]] = None,
                 config: Optional[BaselineConfig] = None):
        """初始化性能基线管理器
        
        Args:
            baseline_file: 基线数据文件路径
            config: 基线配置
        """
        self.config = config or BaselineConfig()
        self.baseline_file = Path(baseline_file) if baseline_file else Path("performance_baseline.json")
        self.baselines: Dict[str, List[PerformanceMetric]] = {}
        self.current_session: List[PerformanceMetric] = []
        
        # 确保基线文件目录存在
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载现有基线数据
        self._load_baselines()
        
        logger.info("性能基线管理器初始化完成", 
                   baseline_file=str(self.baseline_file),
                   config=asdict(self.config))
    
    def add_metric(self, 
                   metric_name: str, 
                   value: float, 
                   unit: str = "ms",
                   context: Optional[Dict[str, Any]] = None) -> None:
        """添加性能指标
        
        Args:
            metric_name: 指标名称
            value: 指标值
            unit: 单位
            context: 上下文信息
        """
        metric = PerformanceMetric(
            name=metric_name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            context=context or {}
        )
        
        self.current_session.append(metric)
        
        # 添加到基线数据
        if metric_name not in self.baselines:
            self.baselines[metric_name] = []
        
        self.baselines[metric_name].append(metric)
        
        # 限制样本数量
        if len(self.baselines[metric_name]) > self.config.max_samples:
            self.baselines[metric_name] = self.baselines[metric_name][-self.config.max_samples:]
        
        logger.debug("添加性能指标", 
                    metric_name=metric_name, 
                    value=value, 
                    unit=unit)
    
    def compare_with_baseline(self, 
                             metric_name: str, 
                             current_value: float) -> Dict[str, Any]:
        """与基线比较性能指标
        
        Args:
            metric_name: 指标名称
            current_value: 当前值
            
        Returns:
            比较结果字典
        """
        if metric_name not in self.baselines or len(self.baselines[metric_name]) < self.config.min_samples:
            return {
                "result": ComparisonResult.NO_BASELINE,
                "message": f"指标 {metric_name} 没有足够的基线数据",
                "baseline_samples": len(self.baselines.get(metric_name, [])),
                "required_samples": self.config.min_samples
            }
        
        baseline_values = [m.value for m in self.baselines[metric_name]]
        baseline_avg = sum(baseline_values) / len(baseline_values)
        
        # 计算差异百分比
        diff_percentage = ((current_value - baseline_avg) / baseline_avg) * 100
        
        # 判断结果
        if abs(diff_percentage) <= self.config.tolerance_percentage:
            result = ComparisonResult.SIMILAR
        elif diff_percentage > 0:
            result = ComparisonResult.WORSE
        else:
            result = ComparisonResult.BETTER
        
        return {
            "result": result,
            "current_value": current_value,
            "baseline_average": baseline_avg,
            "difference_percentage": diff_percentage,
            "tolerance_percentage": self.config.tolerance_percentage,
            "baseline_samples": len(baseline_values),
            "message": self._generate_comparison_message(result, diff_percentage)
        }
    
    def get_baseline_stats(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """获取基线统计信息
        
        Args:
            metric_name: 指标名称
            
        Returns:
            统计信息字典
        """
        if metric_name not in self.baselines or not self.baselines[metric_name]:
            return None
        
        values = [m.value for m in self.baselines[metric_name]]
        
        # 计算统计值
        avg = sum(values) / len(values)
        min_val = min(values)
        max_val = max(values)
        
        # 计算标准差
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        return {
            "metric_name": metric_name,
            "sample_count": len(values),
            "average": avg,
            "minimum": min_val,
            "maximum": max_val,
            "standard_deviation": std_dev,
            "unit": self.baselines[metric_name][0].unit if self.baselines[metric_name] else "unknown"
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """生成性能报告
        
        Returns:
            性能报告字典
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "session_metrics": len(self.current_session),
            "total_baselines": len(self.baselines),
            "config": asdict(self.config),
            "metrics": {},
            "summary": {
                "better_count": 0,
                "worse_count": 0,
                "similar_count": 0,
                "no_baseline_count": 0
            }
        }
        
        # 分析每个指标
        for metric in self.current_session:
            comparison = self.compare_with_baseline(metric.name, metric.value)
            stats = self.get_baseline_stats(metric.name)
            
            report["metrics"][metric.name] = {
                "current_metric": metric.to_dict(),
                "comparison": comparison,
                "baseline_stats": stats
            }
            
            # 更新摘要统计
            result = comparison["result"]
            if result == ComparisonResult.BETTER:
                report["summary"]["better_count"] += 1
            elif result == ComparisonResult.WORSE:
                report["summary"]["worse_count"] += 1
            elif result == ComparisonResult.SIMILAR:
                report["summary"]["similar_count"] += 1
            else:
                report["summary"]["no_baseline_count"] += 1
        
        return report
    
    def save_baselines(self) -> None:
        """保存基线数据到文件"""
        try:
            # 清理过期数据
            self._cleanup_old_data()
            
            # 准备保存数据
            save_data = {
                "config": asdict(self.config),
                "last_updated": datetime.now().isoformat(),
                "baselines": {}
            }
            
            for metric_name, metrics in self.baselines.items():
                save_data["baselines"][metric_name] = [m.to_dict() for m in metrics]
            
            # 写入文件
            with open(self.baseline_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            logger.info("基线数据保存成功", file=str(self.baseline_file))
            
        except Exception as e:
            logger.error("保存基线数据失败", error=str(e), file=str(self.baseline_file))
            raise
    
    def clear_session(self) -> None:
        """清空当前会话数据"""
        self.current_session.clear()
        logger.debug("当前会话数据已清空")
    
    def reset_baselines(self, metric_name: Optional[str] = None) -> None:
        """重置基线数据
        
        Args:
            metric_name: 指定重置的指标名称，None表示重置所有
        """
        if metric_name:
            if metric_name in self.baselines:
                del self.baselines[metric_name]
                logger.info("重置指标基线", metric_name=metric_name)
        else:
            self.baselines.clear()
            logger.info("重置所有基线数据")
    
    def _load_baselines(self) -> None:
        """从文件加载基线数据"""
        if not self.baseline_file.exists():
            logger.info("基线文件不存在，将创建新的基线", file=str(self.baseline_file))
            return
        
        try:
            with open(self.baseline_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载配置（如果存在）
            if "config" in data:
                saved_config = data["config"]
                # 更新配置，但保留当前设置的优先级
                for key, value in saved_config.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
            
            # 加载基线数据
            if "baselines" in data:
                for metric_name, metric_list in data["baselines"].items():
                    self.baselines[metric_name] = [
                        PerformanceMetric.from_dict(m) for m in metric_list
                    ]
            
            logger.info("基线数据加载成功", 
                       file=str(self.baseline_file),
                       metrics_count=len(self.baselines))
            
        except Exception as e:
            logger.error("加载基线数据失败", error=str(e), file=str(self.baseline_file))
            # 不抛出异常，继续使用空基线
    
    def _cleanup_old_data(self) -> None:
        """清理过期数据"""
        cutoff_date = datetime.now().timestamp() - (self.config.retention_days * 24 * 3600)
        
        for metric_name in list(self.baselines.keys()):
            original_count = len(self.baselines[metric_name])
            self.baselines[metric_name] = [
                m for m in self.baselines[metric_name]
                if m.timestamp.timestamp() > cutoff_date
            ]
            
            cleaned_count = original_count - len(self.baselines[metric_name])
            if cleaned_count > 0:
                logger.debug("清理过期数据", 
                           metric_name=metric_name, 
                           cleaned_count=cleaned_count)
    
    def _generate_comparison_message(self, 
                                   result: ComparisonResult, 
                                   diff_percentage: float) -> str:
        """生成比较结果消息"""
        if result == ComparisonResult.BETTER:
            return f"性能提升 {abs(diff_percentage):.1f}%"
        elif result == ComparisonResult.WORSE:
            return f"性能下降 {abs(diff_percentage):.1f}%"
        elif result == ComparisonResult.SIMILAR:
            return f"性能稳定 (差异 {abs(diff_percentage):.1f}%)"
        else:
            return "无基线数据"
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if self.config.auto_update:
            self.save_baselines()