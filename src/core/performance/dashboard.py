"""性能监控仪表板

提供实时性能数据可视化和监控功能，包括：
- 实时性能指标展示
- 性能趋势图表
- 瓶颈识别和告警
- 优化建议展示
- 历史数据对比
"""

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class DashboardConfig:
    """仪表板配置"""

    refresh_interval: int = 5  # 刷新间隔（秒）
    max_data_points: int = 100  # 最大数据点数
    alert_thresholds: Dict[str, float] = None
    chart_colors: Dict[str, str] = None
    enable_real_time: bool = True
    export_format: str = "json"  # json, csv, html

    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "load_time_ms": 3000,
                "lcp": 2500,
                "fid": 100,
                "cls": 0.1,
            }

        if self.chart_colors is None:
            self.chart_colors = {
                "excellent": "#4CAF50",
                "good": "#8BC34A",
                "fair": "#FFC107",
                "poor": "#FF9800",
                "critical": "#F44336",
            }


class PerformanceDashboard:
    """性能监控仪表板

    提供实时性能数据可视化和监控功能。
    """

    def __init__(self, config: Optional[DashboardConfig] = None):
        """初始化仪表板

        Args:
            config: 仪表板配置
        """
        self.config = config or DashboardConfig()
        self.data_history: List[Dict[str, Any]] = []
        self.alerts: List[Dict[str, Any]] = []
        self.is_monitoring = False
        self.start_time = None

        logger.info("性能监控仪表板初始化完成", config=asdict(self.config))

    def start_monitoring(self) -> None:
        """开始监控"""
        self.is_monitoring = True
        self.start_time = datetime.now()
        logger.info("开始性能监控")

    def stop_monitoring(self) -> None:
        """停止监控"""
        self.is_monitoring = False
        logger.info("停止性能监控")

    def add_performance_data(self, data: Dict[str, Any]) -> None:
        """添加性能数据

        Args:
            data: 性能数据
        """
        # 添加时间戳
        data_with_timestamp = {"timestamp": datetime.now().isoformat(), "data": data}

        self.data_history.append(data_with_timestamp)

        # 限制历史数据数量
        if len(self.data_history) > self.config.max_data_points:
            self.data_history = self.data_history[-self.config.max_data_points :]

        # 检查告警
        self._check_alerts(data)

        logger.debug("添加性能数据", data_points=len(self.data_history))

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据

        Returns:
            仪表板数据
        """
        if not self.data_history:
            return self._get_empty_dashboard()

        latest_data = self.data_history[-1]["data"]

        dashboard_data = {
            "status": {
                "is_monitoring": self.is_monitoring,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "data_points": len(self.data_history),
                "last_update": self.data_history[-1]["timestamp"],
            },
            "current_metrics": self._format_current_metrics(latest_data),
            "performance_summary": self._generate_performance_summary(),
            "charts": self._generate_chart_data(),
            "alerts": self._get_recent_alerts(),
            "bottlenecks": self._get_current_bottlenecks(latest_data),
            "suggestions": self._get_optimization_suggestions(latest_data),
            "trends": self._analyze_recent_trends(),
            "health_score": self._calculate_health_score(latest_data),
        }

        return dashboard_data

    def _get_empty_dashboard(self) -> Dict[str, Any]:
        """获取空仪表板数据"""
        return {
            "status": {
                "is_monitoring": self.is_monitoring,
                "start_time": None,
                "data_points": 0,
                "last_update": None,
            },
            "current_metrics": {},
            "performance_summary": {
                "total_tests": 0,
                "avg_load_time": 0,
                "success_rate": 0,
            },
            "charts": [],
            "alerts": [],
            "bottlenecks": [],
            "suggestions": [],
            "trends": [],
            "health_score": 100,
        }

    def _format_current_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化当前指标"""
        metrics = data.get("metrics", {})

        formatted_metrics = {
            "page_load": {},
            "web_vitals": {},
            "user_actions": {},
            "resources": {},
        }

        # 页面加载指标
        page_load = metrics.get("page_load", {})
        if page_load:
            formatted_metrics["page_load"] = {
                "load_time": {
                    "value": page_load.get("load_time_ms", 0),
                    "unit": "ms",
                    "status": self._get_metric_status(
                        "load_time_ms", page_load.get("load_time_ms", 0)
                    ),
                },
                "dom_ready": {
                    "value": page_load.get("dom_ready_ms", 0),
                    "unit": "ms",
                    "status": self._get_metric_status(
                        "dom_ready_ms", page_load.get("dom_ready_ms", 0)
                    ),
                },
                "response_time": {
                    "value": page_load.get("response_time_ms", 0),
                    "unit": "ms",
                    "status": self._get_metric_status(
                        "response_time_ms", page_load.get("response_time_ms", 0)
                    ),
                },
            }

        # Web Vitals指标
        web_vitals = metrics.get("web_vitals", {})
        if web_vitals:
            formatted_metrics["web_vitals"] = {
                "lcp": {
                    "value": web_vitals.get("lcp", 0),
                    "unit": "ms",
                    "status": self._get_metric_status("lcp", web_vitals.get("lcp", 0)),
                },
                "fid": {
                    "value": web_vitals.get("fid", 0),
                    "unit": "ms",
                    "status": self._get_metric_status("fid", web_vitals.get("fid", 0)),
                },
                "cls": {
                    "value": web_vitals.get("cls", 0),
                    "unit": "",
                    "status": self._get_metric_status("cls", web_vitals.get("cls", 0)),
                },
            }

        # 用户操作指标
        actions = metrics.get("actions", [])
        if actions:
            total_time = sum(action.get("execution_time_ms", 0) for action in actions)
            success_count = sum(1 for action in actions if action.get("success", True))

            formatted_metrics["user_actions"] = {
                "total_actions": len(actions),
                "success_rate": (success_count / len(actions)) * 100 if actions else 0,
                "avg_execution_time": total_time / len(actions) if actions else 0,
            }

        return formatted_metrics

    def _get_metric_status(self, metric_name: str, value: float) -> str:
        """获取指标状态"""
        thresholds = {
            "load_time_ms": {"good": 2000, "needs_improvement": 4000},
            "dom_ready_ms": {"good": 1500, "needs_improvement": 3000},
            "response_time_ms": {"good": 500, "needs_improvement": 1000},
            "lcp": {"good": 2500, "needs_improvement": 4000},
            "fid": {"good": 100, "needs_improvement": 300},
            "cls": {"good": 0.1, "needs_improvement": 0.25},
        }

        threshold = thresholds.get(metric_name, {})

        if value <= threshold.get("good", 0):
            return "excellent"
        elif value <= threshold.get("needs_improvement", float("inf")):
            return "good"
        else:
            return "poor"

    def _generate_performance_summary(self) -> Dict[str, Any]:
        """生成性能摘要"""
        if not self.data_history:
            return {"total_tests": 0, "avg_load_time": 0, "success_rate": 0}

        total_tests = len(self.data_history)
        load_times = []
        success_count = 0

        for entry in self.data_history:
            data = entry["data"]
            metrics = data.get("metrics", {})
            page_load = metrics.get("page_load", {})

            if "load_time_ms" in page_load:
                load_times.append(page_load["load_time_ms"])

            # 假设如果有指标数据就算成功
            if metrics:
                success_count += 1

        avg_load_time = sum(load_times) / len(load_times) if load_times else 0
        success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0

        return {
            "total_tests": total_tests,
            "avg_load_time": round(avg_load_time, 2),
            "success_rate": round(success_rate, 2),
        }

    def _generate_chart_data(self) -> List[Dict[str, Any]]:
        """生成图表数据"""
        charts = []

        if len(self.data_history) < 2:
            return charts

        # 页面加载时间趋势图
        load_time_chart = self._create_time_series_chart(
            "页面加载时间趋势", "load_time_ms", "page_load", "ms"
        )
        if load_time_chart:
            charts.append(load_time_chart)

        # Web Vitals趋势图
        lcp_chart = self._create_time_series_chart("LCP趋势", "lcp", "web_vitals", "ms")
        if lcp_chart:
            charts.append(lcp_chart)

        # 性能分布饼图
        performance_distribution = self._create_performance_distribution_chart()
        if performance_distribution:
            charts.append(performance_distribution)

        return charts

    def _create_time_series_chart(
        self, title: str, metric_name: str, category: str, unit: str
    ) -> Optional[Dict[str, Any]]:
        """创建时间序列图表"""
        data_points = []

        for entry in self.data_history[-20:]:  # 最近20个数据点
            timestamp = entry["timestamp"]
            metrics = entry["data"].get("metrics", {})
            category_data = metrics.get(category, {})

            if metric_name in category_data:
                data_points.append(
                    {"timestamp": timestamp, "value": category_data[metric_name]}
                )

        if not data_points:
            return None

        return {
            "type": "line",
            "title": title,
            "data": data_points,
            "config": {
                "x_axis": "timestamp",
                "y_axis": "value",
                "unit": unit,
                "color": "#2196F3",
            },
        }

    def _create_performance_distribution_chart(self) -> Optional[Dict[str, Any]]:
        """创建性能分布饼图"""
        if not self.data_history:
            return None

        status_counts = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}

        for entry in self.data_history:
            data = entry["data"]
            metrics = data.get("metrics", {})
            page_load = metrics.get("page_load", {})

            load_time = page_load.get("load_time_ms", 0)
            status = self._get_metric_status("load_time_ms", load_time)

            if status in status_counts:
                status_counts[status] += 1
            else:
                status_counts["fair"] += 1

        data_points = [
            {
                "label": "优秀",
                "value": status_counts["excellent"],
                "color": self.config.chart_colors["excellent"],
            },
            {
                "label": "良好",
                "value": status_counts["good"],
                "color": self.config.chart_colors["good"],
            },
            {
                "label": "一般",
                "value": status_counts["fair"],
                "color": self.config.chart_colors["fair"],
            },
            {
                "label": "较差",
                "value": status_counts["poor"],
                "color": self.config.chart_colors["poor"],
            },
        ]

        # 过滤掉值为0的项
        data_points = [point for point in data_points if point["value"] > 0]

        if not data_points:
            return None

        return {
            "type": "pie",
            "title": "性能分布",
            "data": data_points,
            "config": {"show_legend": True, "show_percentage": True},
        }

    def _check_alerts(self, data: Dict[str, Any]) -> None:
        """检查告警"""
        metrics = data.get("metrics", {})

        # 检查页面加载时间告警
        page_load = metrics.get("page_load", {})
        for metric_name, threshold in self.config.alert_thresholds.items():
            if metric_name in page_load:
                value = page_load[metric_name]
                if value > threshold:
                    self._add_alert(
                        {
                            "type": "performance_threshold",
                            "metric": metric_name,
                            "value": value,
                            "threshold": threshold,
                            "severity": "high" if value > threshold * 1.5 else "medium",
                            "message": f"{metric_name} ({value}) 超过阈值 ({threshold})",
                        }
                    )

        # 检查Web Vitals告警
        web_vitals = metrics.get("web_vitals", {})
        for metric_name, threshold in self.config.alert_thresholds.items():
            if metric_name in web_vitals:
                value = web_vitals[metric_name]
                if value > threshold:
                    self._add_alert(
                        {
                            "type": "web_vitals_threshold",
                            "metric": metric_name,
                            "value": value,
                            "threshold": threshold,
                            "severity": "high",
                            "message": f"Web Vitals {metric_name} ({value}) 超过阈值 ({threshold})",
                        }
                    )

    def _add_alert(self, alert: Dict[str, Any]) -> None:
        """添加告警"""
        alert["timestamp"] = datetime.now().isoformat()
        alert["id"] = f"{alert['type']}_{alert['metric']}_{int(time.time())}"

        self.alerts.append(alert)

        # 限制告警数量
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

        logger.warning("性能告警", alert=alert)

    def _get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取最近的告警"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_alerts = []
        for alert in self.alerts:
            alert_time = datetime.fromisoformat(alert["timestamp"])
            if alert_time > cutoff_time:
                recent_alerts.append(alert)

        return sorted(recent_alerts, key=lambda x: x["timestamp"], reverse=True)

    def _get_current_bottlenecks(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取当前瓶颈"""
        # 这里可以集成分析引擎的瓶颈识别结果
        analysis_result = data.get("analysis_result", {})
        return analysis_result.get("bottlenecks", [])

    def _get_optimization_suggestions(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """获取优化建议"""
        # 这里可以集成分析引擎的优化建议
        analysis_result = data.get("analysis_result", {})
        return analysis_result.get("suggestions", [])

    def _analyze_recent_trends(self) -> List[Dict[str, Any]]:
        """分析最近趋势"""
        if len(self.data_history) < 5:
            return []

        trends = []

        # 分析页面加载时间趋势
        load_times = []
        for entry in self.data_history[-10:]:  # 最近10个数据点
            metrics = entry["data"].get("metrics", {})
            page_load = metrics.get("page_load", {})
            if "load_time_ms" in page_load:
                load_times.append(page_load["load_time_ms"])

        if len(load_times) >= 3:
            trend = self._calculate_simple_trend(load_times)
            trends.append(
                {
                    "metric": "页面加载时间",
                    "direction": trend["direction"],
                    "change_percentage": trend["change_percentage"],
                    "confidence": trend["confidence"],
                }
            )

        return trends

    def _calculate_simple_trend(self, values: List[float]) -> Dict[str, Any]:
        """计算简单趋势"""
        if len(values) < 2:
            return {"direction": "stable", "change_percentage": 0, "confidence": 0}

        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2 :]

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        change_percentage = (
            ((second_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0
        )

        if abs(change_percentage) < 5:
            direction = "stable"
        elif change_percentage > 0:
            direction = "degrading"  # 对于性能指标，增加意味着变差
        else:
            direction = "improving"

        confidence = min(abs(change_percentage) / 20, 1.0)  # 基于变化幅度计算置信度

        return {
            "direction": direction,
            "change_percentage": abs(change_percentage),
            "confidence": confidence,
        }

    def _calculate_health_score(self, data: Dict[str, Any]) -> int:
        """计算健康评分"""
        # 这里可以集成分析引擎的健康评分
        analysis_result = data.get("analysis_result", {})
        summary = analysis_result.get("summary", {})
        return summary.get("health_score", 100)

    def export_data(self, file_path: str, format_type: str = "json") -> bool:
        """导出数据

        Args:
            file_path: 导出文件路径
            format_type: 导出格式 (json, csv, html)

        Returns:
            是否导出成功
        """
        try:
            export_data = {
                "export_time": datetime.now().isoformat(),
                "config": asdict(self.config),
                "data_history": self.data_history,
                "alerts": self.alerts,
                "dashboard_data": self.get_dashboard_data(),
            }

            if format_type.lower() == "json":
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)

            elif format_type.lower() == "csv":
                import csv

                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)

                    # 写入表头
                    writer.writerow(
                        ["时间戳", "页面加载时间(ms)", "LCP(ms)", "FID(ms)", "CLS"]
                    )

                    # 写入数据
                    for entry in self.data_history:
                        timestamp = entry["timestamp"]
                        metrics = entry["data"].get("metrics", {})
                        page_load = metrics.get("page_load", {})
                        web_vitals = metrics.get("web_vitals", {})

                        writer.writerow(
                            [
                                timestamp,
                                page_load.get("load_time_ms", ""),
                                web_vitals.get("lcp", ""),
                                web_vitals.get("fid", ""),
                                web_vitals.get("cls", ""),
                            ]
                        )

            elif format_type.lower() == "html":
                html_content = self._generate_html_report(export_data)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)

            else:
                logger.error("不支持的导出格式", format_type=format_type)
                return False

            logger.info("数据导出成功", file_path=file_path, format_type=format_type)
            return True

        except Exception as e:
            logger.error("数据导出失败", error=str(e), file_path=file_path)
            return False

    def _generate_html_report(self, data: Dict[str, Any]) -> str:
        """生成HTML报告"""
        dashboard_data = data["dashboard_data"]

        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>性能监控报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .excellent {{ background-color: #e8f5e8; }}
        .good {{ background-color: #f0f8e8; }}
        .poor {{ background-color: #ffeaea; }}
        .alert {{ background-color: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 3px; }}
        .suggestion {{ background-color: #e7f3ff; padding: 10px; margin: 5px 0; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>性能监控报告</h1>
        <p>生成时间: {data['export_time']}</p>
        <p>健康评分: {dashboard_data['health_score']}/100</p>
    </div>
    
    <h2>性能摘要</h2>
    <div class="metric">
        <h3>总测试次数</h3>
        <p>{dashboard_data['performance_summary']['total_tests']}</p>
    </div>
    <div class="metric">
        <h3>平均加载时间</h3>
        <p>{dashboard_data['performance_summary']['avg_load_time']} ms</p>
    </div>
    <div class="metric">
        <h3>成功率</h3>
        <p>{dashboard_data['performance_summary']['success_rate']}%</p>
    </div>
    
    <h2>最近告警</h2>
    {''.join(f'<div class="alert">{alert["message"]} - {alert["timestamp"]}</div>' for alert in dashboard_data['alerts'][:5])}
    
    <h2>优化建议</h2>
    {''.join(f'<div class="suggestion"><strong>{suggestion["title"]}</strong><br>{suggestion["description"]}</div>' for suggestion in dashboard_data['suggestions'][:5])}
    
</body>
</html>
        """

        return html_template

    def clear_data(self) -> None:
        """清空数据"""
        self.data_history.clear()
        self.alerts.clear()
        logger.info("仪表板数据已清空")

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.data_history:
            return {}

        # 计算各种统计指标
        load_times = []
        success_count = 0

        for entry in self.data_history:
            data = entry["data"]
            metrics = data.get("metrics", {})
            page_load = metrics.get("page_load", {})

            if "load_time_ms" in page_load:
                load_times.append(page_load["load_time_ms"])

            if metrics:
                success_count += 1

        statistics = {
            "total_data_points": len(self.data_history),
            "success_rate": (success_count / len(self.data_history)) * 100,
            "total_alerts": len(self.alerts),
        }

        if load_times:
            statistics.update(
                {
                    "load_time_stats": {
                        "min": min(load_times),
                        "max": max(load_times),
                        "avg": sum(load_times) / len(load_times),
                        "median": sorted(load_times)[len(load_times) // 2],
                    }
                }
            )

        return statistics
