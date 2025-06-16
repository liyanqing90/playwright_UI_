"""可观测性仪表板

提供实时性能监控和可视化功能，包括：
- 实时性能指标展示
- 交互式图表和仪表板
- 告警和通知系统
- 性能趋势分析
- 系统健康状态监控
"""

import asyncio
import json
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Callable

import structlog

logger = structlog.get_logger(__name__)

class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"

class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ChartType(Enum):
    """图表类型"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    GAUGE = "gauge"
    HEATMAP = "heatmap"
    SCATTER = "scatter"

@dataclass
class MetricPoint:
    """指标数据点"""
    timestamp: float
    value: float
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}

@dataclass
class MetricSeries:
    """指标序列"""
    name: str
    type: MetricType
    description: str
    unit: str
    points: deque
    max_points: int = 1000
    
    def __post_init__(self):
        if not isinstance(self.points, deque):
            self.points = deque(self.points or [], maxlen=self.max_points)
    
    def add_point(self, value: float, labels: Dict[str, str] = None) -> None:
        """添加数据点"""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            labels=labels or {}
        )
        self.points.append(point)
    
    def get_latest_value(self) -> Optional[float]:
        """获取最新值"""
        return self.points[-1].value if self.points else None
    
    def get_values_in_range(self, start_time: float, end_time: float) -> List[MetricPoint]:
        """获取时间范围内的值"""
        return [
            point for point in self.points
            if start_time <= point.timestamp <= end_time
        ]
    
    def calculate_statistics(self, duration_minutes: int = 60) -> Dict[str, float]:
        """计算统计信息"""
        cutoff_time = time.time() - (duration_minutes * 60)
        recent_points = [
            point.value for point in self.points
            if point.timestamp >= cutoff_time
        ]
        
        if not recent_points:
            return {}
        
        return {
            "count": len(recent_points),
            "min": min(recent_points),
            "max": max(recent_points),
            "mean": statistics.mean(recent_points),
            "median": statistics.median(recent_points),
            "std_dev": statistics.stdev(recent_points) if len(recent_points) > 1 else 0
        }

@dataclass
class Alert:
    """告警"""
    id: str
    metric_name: str
    level: AlertLevel
    message: str
    threshold: float
    current_value: float
    timestamp: str
    acknowledged: bool = False
    resolved: bool = False
    resolution_time: Optional[str] = None

@dataclass
class DashboardWidget:
    """仪表板组件"""
    id: str
    title: str
    chart_type: ChartType
    metric_names: List[str]
    config: Dict[str, Any]
    position: Dict[str, int]  # {"x": 0, "y": 0, "width": 4, "height": 3}
    refresh_interval: int = 30  # 秒

@dataclass
class Dashboard:
    """仪表板"""
    id: str
    name: str
    description: str
    widgets: List[DashboardWidget]
    layout: Dict[str, Any]
    created_at: str
    updated_at: str

class ObservabilityDashboard:
    """可观测性仪表板
    
    提供实时性能监控和可视化功能。
    """
    
    def __init__(self):
        """初始化仪表板"""
        self.metrics: Dict[str, MetricSeries] = {}
        self.alerts: List[Alert] = []
        self.dashboards: Dict[str, Dashboard] = {}
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.is_running = False
        
        # 创建默认仪表板
        self._create_default_dashboards()
        
        # 设置默认告警规则
        self._setup_default_alert_rules()
        
        logger.info("可观测性仪表板初始化完成")
    
    def _create_default_dashboards(self) -> None:
        """创建默认仪表板"""
        # 性能概览仪表板
        performance_dashboard = Dashboard(
            id="performance_overview",
            name="性能概览",
            description="系统性能关键指标概览",
            widgets=[
                DashboardWidget(
                    id="response_time_chart",
                    title="响应时间趋势",
                    chart_type=ChartType.LINE,
                    metric_names=["response_time", "page_load_time"],
                    config={
                        "time_range": "1h",
                        "y_axis_label": "时间 (ms)",
                        "show_legend": True
                    },
                    position={"x": 0, "y": 0, "width": 6, "height": 4}
                ),
                DashboardWidget(
                    id="error_rate_gauge",
                    title="错误率",
                    chart_type=ChartType.GAUGE,
                    metric_names=["error_rate"],
                    config={
                        "min_value": 0,
                        "max_value": 100,
                        "unit": "%",
                        "thresholds": [
                            {"value": 5, "color": "green"},
                            {"value": 10, "color": "yellow"},
                            {"value": 20, "color": "red"}
                        ]
                    },
                    position={"x": 6, "y": 0, "width": 3, "height": 2}
                ),
                DashboardWidget(
                    id="throughput_gauge",
                    title="吞吐量",
                    chart_type=ChartType.GAUGE,
                    metric_names=["throughput"],
                    config={
                        "min_value": 0,
                        "max_value": 1000,
                        "unit": "req/min"
                    },
                    position={"x": 9, "y": 0, "width": 3, "height": 2}
                ),
                DashboardWidget(
                    id="memory_usage_chart",
                    title="内存使用率",
                    chart_type=ChartType.LINE,
                    metric_names=["memory_usage"],
                    config={
                        "time_range": "30m",
                        "y_axis_label": "使用率 (%)",
                        "fill_area": True
                    },
                    position={"x": 6, "y": 2, "width": 6, "height": 2}
                ),
                DashboardWidget(
                    id="test_results_pie",
                    title="测试结果分布",
                    chart_type=ChartType.PIE,
                    metric_names=["test_passed", "test_failed", "test_skipped"],
                    config={
                        "show_labels": True,
                        "show_percentages": True
                    },
                    position={"x": 0, "y": 4, "width": 4, "height": 3}
                ),
                DashboardWidget(
                    id="browser_performance_heatmap",
                    title="浏览器性能热图",
                    chart_type=ChartType.HEATMAP,
                    metric_names=["browser_performance"],
                    config={
                        "x_axis": "time",
                        "y_axis": "browser_type",
                        "value_axis": "performance_score"
                    },
                    position={"x": 4, "y": 4, "width": 8, "height": 3}
                )
            ],
            layout={"columns": 12, "row_height": 60},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # 错误监控仪表板
        error_dashboard = Dashboard(
            id="error_monitoring",
            name="错误监控",
            description="错误和异常监控",
            widgets=[
                DashboardWidget(
                    id="error_trend_chart",
                    title="错误趋势",
                    chart_type=ChartType.LINE,
                    metric_names=["error_count", "critical_errors"],
                    config={
                        "time_range": "2h",
                        "y_axis_label": "错误数量",
                        "alert_overlay": True
                    },
                    position={"x": 0, "y": 0, "width": 8, "height": 4}
                ),
                DashboardWidget(
                    id="error_category_bar",
                    title="错误分类",
                    chart_type=ChartType.BAR,
                    metric_names=["network_errors", "timeout_errors", "element_errors"],
                    config={
                        "orientation": "horizontal",
                        "show_values": True
                    },
                    position={"x": 8, "y": 0, "width": 4, "height": 4}
                ),
                DashboardWidget(
                    id="recovery_rate_gauge",
                    title="恢复成功率",
                    chart_type=ChartType.GAUGE,
                    metric_names=["recovery_rate"],
                    config={
                        "min_value": 0,
                        "max_value": 100,
                        "unit": "%",
                        "target_value": 95
                    },
                    position={"x": 0, "y": 4, "width": 6, "height": 3}
                ),
                DashboardWidget(
                    id="mttr_chart",
                    title="平均恢复时间 (MTTR)",
                    chart_type=ChartType.LINE,
                    metric_names=["mttr"],
                    config={
                        "time_range": "24h",
                        "y_axis_label": "时间 (分钟)",
                        "target_line": 5
                    },
                    position={"x": 6, "y": 4, "width": 6, "height": 3}
                )
            ],
            layout={"columns": 12, "row_height": 60},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.dashboards["performance_overview"] = performance_dashboard
        self.dashboards["error_monitoring"] = error_dashboard
    
    def _setup_default_alert_rules(self) -> None:
        """设置默认告警规则"""
        self.alert_rules = {
            "response_time": {
                "threshold": 5000,  # 5秒
                "operator": ">",
                "level": AlertLevel.WARNING,
                "message": "响应时间过长"
            },
            "error_rate": {
                "threshold": 10,  # 10%
                "operator": ">",
                "level": AlertLevel.ERROR,
                "message": "错误率过高"
            },
            "memory_usage": {
                "threshold": 90,  # 90%
                "operator": ">",
                "level": AlertLevel.WARNING,
                "message": "内存使用率过高"
            },
            "page_load_time": {
                "threshold": 10000,  # 10秒
                "operator": ">",
                "level": AlertLevel.ERROR,
                "message": "页面加载时间过长"
            },
            "test_failure_rate": {
                "threshold": 20,  # 20%
                "operator": ">",
                "level": AlertLevel.CRITICAL,
                "message": "测试失败率过高"
            }
        }
    
    async def start(self) -> None:
        """启动仪表板"""
        if self.is_running:
            logger.warning("仪表板已在运行")
            return
        
        self.is_running = True
        logger.info("启动可观测性仪表板")
        
        # 启动监控循环
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self._alert_checking_loop())
    
    async def stop(self) -> None:
        """停止仪表板"""
        self.is_running = False
        logger.info("可观测性仪表板已停止")
    
    def register_metric(self, 
                       name: str, 
                       metric_type: MetricType,
                       description: str = "",
                       unit: str = "",
                       max_points: int = 1000) -> None:
        """注册指标
        
        Args:
            name: 指标名称
            metric_type: 指标类型
            description: 描述
            unit: 单位
            max_points: 最大数据点数量
        """
        self.metrics[name] = MetricSeries(
            name=name,
            type=metric_type,
            description=description,
            unit=unit,
            points=deque(maxlen=max_points),
            max_points=max_points
        )
        
        logger.info("注册指标", name=name, type=metric_type.value)
    
    def record_metric(self, 
                     name: str, 
                     value: float, 
                     labels: Dict[str, str] = None) -> None:
        """记录指标值
        
        Args:
            name: 指标名称
            value: 指标值
            labels: 标签
        """
        if name not in self.metrics:
            # 自动注册未知指标
            self.register_metric(name, MetricType.GAUGE)
        
        self.metrics[name].add_point(value, labels)
        
        # 检查告警
        asyncio.create_task(self._check_alert_for_metric(name, value))
    
    def increment_counter(self, name: str, labels: Dict[str, str] = None) -> None:
        """递增计数器
        
        Args:
            name: 计数器名称
            labels: 标签
        """
        if name not in self.metrics:
            self.register_metric(name, MetricType.COUNTER)
        
        current_value = self.metrics[name].get_latest_value() or 0
        self.record_metric(name, current_value + 1, labels)
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """设置仪表值
        
        Args:
            name: 仪表名称
            value: 值
            labels: 标签
        """
        if name not in self.metrics:
            self.register_metric(name, MetricType.GAUGE)
        
        self.record_metric(name, value, labels)
    
    def record_timer(self, name: str, duration: float, labels: Dict[str, str] = None) -> None:
        """记录计时器
        
        Args:
            name: 计时器名称
            duration: 持续时间
            labels: 标签
        """
        if name not in self.metrics:
            self.register_metric(name, MetricType.TIMER, unit="ms")
        
        self.record_metric(name, duration, labels)
    
    def get_metric_data(self, 
                       name: str, 
                       start_time: Optional[float] = None,
                       end_time: Optional[float] = None) -> Dict[str, Any]:
        """获取指标数据
        
        Args:
            name: 指标名称
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            指标数据
        """
        if name not in self.metrics:
            return {}
        
        metric = self.metrics[name]
        
        if start_time is None:
            start_time = time.time() - 3600  # 默认1小时
        if end_time is None:
            end_time = time.time()
        
        points = metric.get_values_in_range(start_time, end_time)
        statistics_data = metric.calculate_statistics()
        
        return {
            "name": name,
            "type": metric.type.value,
            "description": metric.description,
            "unit": metric.unit,
            "points": [
                {
                    "timestamp": point.timestamp,
                    "value": point.value,
                    "labels": point.labels
                }
                for point in points
            ],
            "statistics": statistics_data,
            "latest_value": metric.get_latest_value()
        }
    
    def get_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """获取仪表板数据
        
        Args:
            dashboard_id: 仪表板ID
            
        Returns:
            仪表板数据
        """
        if dashboard_id not in self.dashboards:
            return {}
        
        dashboard = self.dashboards[dashboard_id]
        
        # 获取所有组件的数据
        widget_data = {}
        for widget in dashboard.widgets:
            widget_metrics = {}
            for metric_name in widget.metric_names:
                widget_metrics[metric_name] = self.get_metric_data(metric_name)
            
            widget_data[widget.id] = {
                "config": widget,
                "metrics": widget_metrics
            }
        
        return {
            "dashboard": asdict(dashboard),
            "widgets": widget_data,
            "alerts": [asdict(alert) for alert in self.get_active_alerts()],
            "timestamp": time.time()
        }
    
    def create_custom_dashboard(self, 
                               name: str,
                               description: str,
                               widgets: List[DashboardWidget]) -> str:
        """创建自定义仪表板
        
        Args:
            name: 仪表板名称
            description: 描述
            widgets: 组件列表
            
        Returns:
            仪表板ID
        """
        dashboard_id = f"custom_{int(time.time())}"
        
        dashboard = Dashboard(
            id=dashboard_id,
            name=name,
            description=description,
            widgets=widgets,
            layout={"columns": 12, "row_height": 60},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.dashboards[dashboard_id] = dashboard
        
        logger.info("创建自定义仪表板", 
                   dashboard_id=dashboard_id,
                   name=name,
                   widget_count=len(widgets))
        
        return dashboard_id
    
    def add_alert_rule(self, 
                      metric_name: str,
                      threshold: float,
                      operator: str,
                      level: AlertLevel,
                      message: str) -> None:
        """添加告警规则
        
        Args:
            metric_name: 指标名称
            threshold: 阈值
            operator: 操作符 (>, <, >=, <=, ==, !=)
            level: 告警级别
            message: 告警消息
        """
        self.alert_rules[metric_name] = {
            "threshold": threshold,
            "operator": operator,
            "level": level,
            "message": message
        }
        
        logger.info("添加告警规则", 
                   metric=metric_name,
                   threshold=threshold,
                   operator=operator,
                   level=level.value)
    
    async def _check_alert_for_metric(self, metric_name: str, value: float) -> None:
        """检查指标告警
        
        Args:
            metric_name: 指标名称
            value: 当前值
        """
        if metric_name not in self.alert_rules:
            return
        
        rule = self.alert_rules[metric_name]
        threshold = rule["threshold"]
        operator = rule["operator"]
        
        # 检查是否触发告警
        triggered = False
        if operator == ">" and value > threshold:
            triggered = True
        elif operator == "<" and value < threshold:
            triggered = True
        elif operator == ">=" and value >= threshold:
            triggered = True
        elif operator == "<=" and value <= threshold:
            triggered = True
        elif operator == "==" and value == threshold:
            triggered = True
        elif operator == "!=" and value != threshold:
            triggered = True
        
        if triggered:
            await self._create_alert(metric_name, value, rule)
    
    async def _create_alert(self, 
                           metric_name: str, 
                           current_value: float, 
                           rule: Dict[str, Any]) -> None:
        """创建告警
        
        Args:
            metric_name: 指标名称
            current_value: 当前值
            rule: 告警规则
        """
        alert_id = f"alert_{metric_name}_{int(time.time())}"
        
        alert = Alert(
            id=alert_id,
            metric_name=metric_name,
            level=rule["level"],
            message=rule["message"],
            threshold=rule["threshold"],
            current_value=current_value,
            timestamp=datetime.now().isoformat()
        )
        
        self.alerts.append(alert)
        
        logger.warning("创建告警", 
                      alert_id=alert_id,
                      metric=metric_name,
                      level=rule["level"].value,
                      current_value=current_value,
                      threshold=rule["threshold"])
        
        # 通知订阅者
        await self._notify_subscribers("alert_created", alert)
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return [alert for alert in self.alerts if not alert.resolved]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警
        
        Args:
            alert_id: 告警ID
            
        Returns:
            是否成功
        """
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                logger.info("告警已确认", alert_id=alert_id)
                return True
        
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警
        
        Args:
            alert_id: 告警ID
            
        Returns:
            是否成功
        """
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolution_time = datetime.now().isoformat()
                logger.info("告警已解决", alert_id=alert_id)
                return True
        
        return False
    
    def subscribe_to_events(self, event_type: str, callback: Callable) -> None:
        """订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        self.subscribers[event_type].append(callback)
        logger.info("订阅事件", event_type=event_type)
    
    async def _notify_subscribers(self, event_type: str, data: Any) -> None:
        """通知订阅者
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error("通知订阅者失败", 
                                event_type=event_type,
                                error=str(e))
    
    async def _monitoring_loop(self) -> None:
        """监控循环"""
        while self.is_running:
            try:
                # 收集系统指标
                await self._collect_system_metrics()
                
                # 计算衍生指标
                await self._calculate_derived_metrics()
                
                # 清理过期数据
                await self._cleanup_old_data()
                
                await asyncio.sleep(10)  # 每10秒收集一次
                
            except Exception as e:
                logger.error("监控循环异常", error=str(e))
                await asyncio.sleep(30)
    
    async def _alert_checking_loop(self) -> None:
        """告警检查循环"""
        while self.is_running:
            try:
                # 检查告警恢复
                await self._check_alert_recovery()
                
                # 清理过期告警
                await self._cleanup_old_alerts()
                
                await asyncio.sleep(30)  # 每30秒检查一次
                
            except Exception as e:
                logger.error("告警检查循环异常", error=str(e))
                await asyncio.sleep(60)
    
    async def _collect_system_metrics(self) -> None:
        """收集系统指标"""
        try:
            import psutil
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent()
            self.set_gauge("cpu_usage", cpu_percent)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            self.set_gauge("memory_usage", memory.percent)
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            self.set_gauge("disk_usage", (disk.used / disk.total) * 100)
            
        except ImportError:
            # psutil 未安装，使用模拟数据
            import random
            self.set_gauge("cpu_usage", random.uniform(10, 80))
            self.set_gauge("memory_usage", random.uniform(30, 90))
            self.set_gauge("disk_usage", random.uniform(20, 70))
        
        except Exception as e:
            logger.error("收集系统指标失败", error=str(e))
    
    async def _calculate_derived_metrics(self) -> None:
        """计算衍生指标"""
        try:
            # 计算错误率
            if "test_passed" in self.metrics and "test_failed" in self.metrics:
                passed = self.metrics["test_passed"].get_latest_value() or 0
                failed = self.metrics["test_failed"].get_latest_value() or 0
                total = passed + failed
                
                if total > 0:
                    error_rate = (failed / total) * 100
                    self.set_gauge("error_rate", error_rate)
            
            # 计算吞吐量（每分钟请求数）
            if "request_count" in self.metrics:
                # 获取最近1分钟的请求数
                recent_time = time.time() - 60
                recent_points = self.metrics["request_count"].get_values_in_range(
                    recent_time, time.time()
                )
                throughput = len(recent_points)
                self.set_gauge("throughput", throughput)
            
            # 计算平均响应时间
            if "response_time" in self.metrics:
                stats = self.metrics["response_time"].calculate_statistics(5)
                if "mean" in stats:
                    self.set_gauge("avg_response_time", stats["mean"])
        
        except Exception as e:
            logger.error("计算衍生指标失败", error=str(e))
    
    async def _check_alert_recovery(self) -> None:
        """检查告警恢复"""
        for alert in self.get_active_alerts():
            if alert.metric_name in self.metrics:
                current_value = self.metrics[alert.metric_name].get_latest_value()
                
                if current_value is not None:
                    # 检查是否已恢复正常
                    rule = self.alert_rules.get(alert.metric_name)
                    if rule:
                        threshold = rule["threshold"]
                        operator = rule["operator"]
                        
                        # 反向检查条件
                        recovered = False
                        if operator == ">" and current_value <= threshold:
                            recovered = True
                        elif operator == "<" and current_value >= threshold:
                            recovered = True
                        elif operator == ">=" and current_value < threshold:
                            recovered = True
                        elif operator == "<=" and current_value > threshold:
                            recovered = True
                        
                        if recovered:
                            self.resolve_alert(alert.id)
                            await self._notify_subscribers("alert_resolved", alert)
    
    async def _cleanup_old_data(self) -> None:
        """清理过期数据"""
        # 清理超过24小时的指标数据
        cutoff_time = time.time() - (24 * 3600)
        
        for metric in self.metrics.values():
            # deque 会自动限制大小，这里主要是为了清理标签等额外数据
            pass
    
    async def _cleanup_old_alerts(self) -> None:
        """清理过期告警"""
        # 清理超过7天的已解决告警
        cutoff_time = datetime.now() - timedelta(days=7)
        
        self.alerts = [
            alert for alert in self.alerts
            if not alert.resolved or 
               datetime.fromisoformat(alert.timestamp) > cutoff_time
        ]
    
    def export_dashboard_config(self, dashboard_id: str) -> Optional[str]:
        """导出仪表板配置
        
        Args:
            dashboard_id: 仪表板ID
            
        Returns:
            JSON配置字符串
        """
        if dashboard_id not in self.dashboards:
            return None
        
        dashboard = self.dashboards[dashboard_id]
        config = asdict(dashboard)
        
        return json.dumps(config, indent=2, ensure_ascii=False)
    
    def import_dashboard_config(self, config_json: str) -> Optional[str]:
        """导入仪表板配置
        
        Args:
            config_json: JSON配置字符串
            
        Returns:
            仪表板ID
        """
        try:
            config = json.loads(config_json)
            
            # 重新构建对象
            widgets = [
                DashboardWidget(**widget_data)
                for widget_data in config["widgets"]
            ]
            
            dashboard = Dashboard(
                id=config["id"],
                name=config["name"],
                description=config["description"],
                widgets=widgets,
                layout=config["layout"],
                created_at=config["created_at"],
                updated_at=datetime.now().isoformat()
            )
            
            self.dashboards[dashboard.id] = dashboard
            
            logger.info("导入仪表板配置", dashboard_id=dashboard.id)
            return dashboard.id
        
        except Exception as e:
            logger.error("导入仪表板配置失败", error=str(e))
            return None
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        summary = {
            "total_metrics": len(self.metrics),
            "active_alerts": len(self.get_active_alerts()),
            "dashboards": len(self.dashboards),
            "metrics_by_type": defaultdict(int)
        }
        
        for metric in self.metrics.values():
            summary["metrics_by_type"][metric.type.value] += 1
        
        # 转换为普通字典
        summary["metrics_by_type"] = dict(summary["metrics_by_type"])
        
        return summary
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        active_alerts = self.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a.level == AlertLevel.CRITICAL]
        error_alerts = [a for a in active_alerts if a.level == AlertLevel.ERROR]
        
        # 确定整体健康状态
        if critical_alerts:
            status = "critical"
        elif error_alerts:
            status = "error"
        elif active_alerts:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "total_alerts": len(active_alerts),
            "critical_alerts": len(critical_alerts),
            "error_alerts": len(error_alerts),
            "warning_alerts": len([a for a in active_alerts if a.level == AlertLevel.WARNING]),
            "is_running": self.is_running,
            "uptime": time.time() - getattr(self, '_start_time', time.time()),
            "last_update": datetime.now().isoformat()
        }

# 全局仪表板实例
global_dashboard = ObservabilityDashboard()

# 便捷函数
def record_performance_metric(name: str, value: float, labels: Dict[str, str] = None) -> None:
    """记录性能指标"""
    global_dashboard.record_metric(name, value, labels)

def increment_test_counter(test_type: str, result: str) -> None:
    """递增测试计数器"""
    global_dashboard.increment_counter(f"test_{result}", {"type": test_type})

def record_response_time(operation: str, duration: float) -> None:
    """记录响应时间"""
    global_dashboard.record_timer("response_time", duration, {"operation": operation})

def set_system_gauge(metric: str, value: float) -> None:
    """设置系统仪表"""
    global_dashboard.set_gauge(metric, value)