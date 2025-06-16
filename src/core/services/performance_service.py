"""性能监控服务模块

提供页面性能监控、指标收集和基线比较功能。
集成PerformanceBaseline进行自动化性能回归检测。
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Protocol

import structlog
from playwright.sync_api import Page

from ..performance.analysis_engine import PerformanceAnalysisEngine
from ..performance.automation_engine import AutomationEngine
from ..performance.error_handler import ErrorHandler
from ..performance.observability_dashboard import global_dashboard
from ..performance.performance_baseline import PerformanceBaseline, BaselineConfig

logger = structlog.get_logger(__name__)

class PerformanceOperations(Protocol):
    """性能监控操作协议"""
    
    def start_monitoring(self, test_name: str) -> None:
        """开始性能监控"""
        ...
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """停止性能监控并返回结果"""
        ...
    
    def measure_page_load(self, url: str, **kwargs) -> Dict[str, Any]:
        """测量页面加载性能"""
        ...
    
    def measure_action_time(self, action_name: str, action_func, *args, **kwargs) -> Dict[str, Any]:
        """测量操作执行时间"""
        ...
    
    def get_web_vitals(self) -> Dict[str, Any]:
        """获取Web Vitals指标"""
        ...
    
    def compare_with_baseline(self, metric_name: str, value: float) -> Dict[str, Any]:
        """与基线比较"""
        ...
    
    def generate_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        ...

class PerformanceService:
    """性能监控服务实现
    
    提供完整的性能监控功能，包括：
    - 页面加载性能测量
    - 用户操作性能测量
    - Web Vitals指标收集
    - 性能基线比较
    - 性能报告生成
    - 智能分析引擎
    - 可观测性仪表板
    - 自动化优化引擎
    - 错误处理和重试机制
    """
    
    def __init__(self, 
                 baseline_config: Optional[BaselineConfig] = None,
                 baseline_file: Optional[str] = None):
        """初始化性能监控服务
        
        Args:
            baseline_config: 基线配置
            baseline_file: 基线文件路径
        """
        self.page: Optional[Page] = None
        self.current_test: Optional[str] = None
        self.start_time: Optional[float] = None
        self.metrics: Dict[str, Any] = {}
        
        # 初始化性能基线管理器
        self.baseline = PerformanceBaseline(
            baseline_file=baseline_file,
            config=baseline_config or BaselineConfig()
        )
        
        # 初始化新的性能组件
        self.analysis_engine = PerformanceAnalysisEngine()
        self.dashboard = global_dashboard
        self.automation_engine = AutomationEngine()
        self.error_handler = ErrorHandler()
        
        # 启动仪表板
        asyncio.create_task(self._start_dashboard())
        
        logger.info("性能监控服务初始化完成，已集成分析引擎和仪表板")
    
    def set_page(self, page: Page) -> None:
        """设置页面对象"""
        self.page = page
        logger.debug("页面对象已设置")
    
    def start_monitoring(self, test_name: str) -> None:
        """开始性能监控
        
        Args:
            test_name: 测试名称
        """
        self.current_test = test_name
        self.start_time = time.time()
        self.metrics.clear()
        
        logger.info("开始性能监控", test_name=test_name)
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """停止性能监控并返回结果
        
        Returns:
            监控结果字典
        """
        if not self.current_test or not self.start_time:
            logger.warning("性能监控未启动")
            return {}
        
        total_time = time.time() - self.start_time
        
        # 添加总时间指标
        self.baseline.add_metric(
            f"{self.current_test}_total_time",
            total_time * 1000,  # 转换为毫秒
            "ms",
            {"test_name": self.current_test}
        )
        
        result = {
            "test_name": self.current_test,
            "total_time_ms": total_time * 1000,
            "metrics": self.metrics.copy(),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("停止性能监控", 
                   test_name=self.current_test, 
                   total_time_ms=total_time * 1000)
        
        # 重置状态
        self.current_test = None
        self.start_time = None
        
        return result
    
    def measure_page_load(self, url: str, **kwargs) -> Dict[str, Any]:
        """测量页面加载性能
        
        Args:
            url: 页面URL
            **kwargs: 额外参数
            
        Returns:
            页面加载性能指标
        """
        if not self.page:
            raise ValueError("页面对象未设置")
        
        start_time = time.time()
        
        try:
            # 导航到页面
            response = self.page.goto(url, **kwargs)
            
            # 等待页面加载完成
            self.page.wait_for_load_state('networkidle')
            
            load_time = (time.time() - start_time) * 1000
            
            # 获取导航时间指标
            navigation_timing = self.page.evaluate("""
                () => {
                    const timing = performance.timing;
                    const navigation = performance.getEntriesByType('navigation')[0];
                    
                    return {
                        domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                        loadComplete: timing.loadEventEnd - timing.navigationStart,
                        domReady: timing.domInteractive - timing.navigationStart,
                        firstPaint: navigation ? navigation.responseStart - navigation.requestStart : 0,
                        responseTime: timing.responseEnd - timing.requestStart
                    };
                }
            """)
            
            # 获取资源加载信息
            resource_timing = self.page.evaluate("""
                () => {
                    const resources = performance.getEntriesByType('resource');
                    return {
                        resourceCount: resources.length,
                        totalSize: resources.reduce((sum, r) => sum + (r.transferSize || 0), 0),
                        slowestResource: Math.max(...resources.map(r => r.duration))
                    };
                }
            """)
            
            metrics = {
                "url": url,
                "load_time_ms": load_time,
                "dom_content_loaded_ms": navigation_timing.get('domContentLoaded', 0),
                "load_complete_ms": navigation_timing.get('loadComplete', 0),
                "dom_ready_ms": navigation_timing.get('domReady', 0),
                "response_time_ms": navigation_timing.get('responseTime', 0),
                "resource_count": resource_timing.get('resourceCount', 0),
                "total_size_bytes": resource_timing.get('totalSize', 0),
                "slowest_resource_ms": resource_timing.get('slowestResource', 0),
                "status_code": response.status if response else 0
            }
            
            # 添加到基线
            test_prefix = self.current_test or "page_load"
            for metric_name, value in metrics.items():
                if isinstance(value, (int, float)) and metric_name.endswith(('_ms', '_bytes')):
                    self.baseline.add_metric(
                        f"{test_prefix}_{metric_name}",
                        value,
                        "ms" if metric_name.endswith('_ms') else "bytes",
                        {"url": url, "test_name": self.current_test}
                    )
            
            # 存储到当前指标
            self.metrics["page_load"] = metrics
            
            # 记录到仪表板
            self.dashboard.record_metric('page_load_time', load_time, {'url': url})
            self.dashboard.record_metric('dom_ready_time', metrics["dom_ready_ms"], {'url': url})
            self.dashboard.record_metric('resource_count', metrics["resource_count"], {'url': url})
            
            logger.info("页面加载性能测量完成", 
                       url=url, 
                       load_time_ms=load_time,
                       dom_ready_ms=metrics["dom_ready_ms"])
            
            return metrics
            
        except Exception as e:
            logger.error("页面加载性能测量失败", url=url, error=str(e))
            raise
    
    def measure_action_time(self, action_name: str, action_func, *args, **kwargs) -> Dict[str, Any]:
        """测量操作执行时间
        
        Args:
            action_name: 操作名称
            action_func: 操作函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            操作性能指标
        """
        start_time = time.time()
        
        try:
            # 执行操作
            result = action_func(*args, **kwargs)
            
            execution_time = (time.time() - start_time) * 1000
            
            metrics = {
                "action_name": action_name,
                "execution_time_ms": execution_time,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
            # 添加到基线
            test_prefix = self.current_test or "action"
            self.baseline.add_metric(
                f"{test_prefix}_{action_name}_time",
                execution_time,
                "ms",
                {"action_name": action_name, "test_name": self.current_test}
            )
            
            # 存储到当前指标
            if "actions" not in self.metrics:
                self.metrics["actions"] = []
            self.metrics["actions"].append(metrics)
            
            # 记录到仪表板
            self.dashboard.record_timer('action_time', execution_time, {'action': action_name})
            self.dashboard.increment_counter('action_success', {'action': action_name})
            
            logger.info("操作性能测量完成", 
                       action_name=action_name, 
                       execution_time_ms=execution_time)
            
            return {"metrics": metrics, "result": result}
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            error_metrics = {
                "action_name": action_name,
                "execution_time_ms": execution_time,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }
            
            if "actions" not in self.metrics:
                self.metrics["actions"] = []
            self.metrics["actions"].append(error_metrics)
            
            # 记录错误到仪表板
            self.dashboard.increment_counter('action_error', {'action': action_name})
            self.dashboard.record_timer('action_time', execution_time, {'action': action_name, 'status': 'error'})
            
            logger.error("操作性能测量失败", 
                        action_name=action_name, 
                        execution_time_ms=execution_time,
                        error=str(e))
            
            raise
    
    def get_web_vitals(self) -> Dict[str, Any]:
        """获取Web Vitals指标
        
        Returns:
            Web Vitals指标字典
        """
        if not self.page:
            raise ValueError("页面对象未设置")
        
        try:
            # 获取Web Vitals指标
            vitals = self.page.evaluate("""
                () => {
                    return new Promise((resolve) => {
                        const vitals = {};
                        
                        // LCP (Largest Contentful Paint)
                        new PerformanceObserver((list) => {
                            const entries = list.getEntries();
                            if (entries.length > 0) {
                                vitals.lcp = entries[entries.length - 1].startTime;
                            }
                        }).observe({entryTypes: ['largest-contentful-paint']});
                        
                        // FID (First Input Delay)
                        new PerformanceObserver((list) => {
                            const entries = list.getEntries();
                            if (entries.length > 0) {
                                vitals.fid = entries[0].processingStart - entries[0].startTime;
                            }
                        }).observe({entryTypes: ['first-input']});
                        
                        // CLS (Cumulative Layout Shift)
                        let clsValue = 0;
                        new PerformanceObserver((list) => {
                            for (const entry of list.getEntries()) {
                                if (!entry.hadRecentInput) {
                                    clsValue += entry.value;
                                }
                            }
                            vitals.cls = clsValue;
                        }).observe({entryTypes: ['layout-shift']});
                        
                        // FCP (First Contentful Paint)
                        new PerformanceObserver((list) => {
                            const entries = list.getEntries();
                            if (entries.length > 0) {
                                vitals.fcp = entries[0].startTime;
                            }
                        }).observe({entryTypes: ['paint']});
                        
                        // 等待一段时间收集指标
                        setTimeout(() => {
                            resolve(vitals);
                        }, 1000);
                    });
                }
            """)
            
            # 添加到基线
            test_prefix = self.current_test or "web_vitals"
            for metric_name, value in vitals.items():
                if isinstance(value, (int, float)):
                    self.baseline.add_metric(
                        f"{test_prefix}_{metric_name}",
                        value,
                        "ms" if metric_name != "cls" else "score",
                        {"metric_type": "web_vital", "test_name": self.current_test}
                    )
            
            # 存储到当前指标
            self.metrics["web_vitals"] = vitals
            
            # 记录到仪表板
            for metric_name, value in vitals.items():
                if isinstance(value, (int, float)):
                    self.dashboard.record_metric(f'web_vital_{metric_name}', value)
            
            logger.info("Web Vitals指标收集完成", vitals=vitals)
            
            return vitals
            
        except Exception as e:
            logger.error("Web Vitals指标收集失败", error=str(e))
            return {}
    
    def compare_with_baseline(self, metric_name: str, value: float) -> Dict[str, Any]:
        """与基线比较
        
        Args:
            metric_name: 指标名称
            value: 当前值
            
        Returns:
            比较结果
        """
        return self.baseline.compare_with_baseline(metric_name, value)
    
    def generate_report(self) -> Dict[str, Any]:
        """生成性能报告
        
        Returns:
            性能报告字典
        """
        baseline_report = self.baseline.generate_report()
        
        # 合并当前会话指标
        report = {
            "current_session": {
                "test_name": self.current_test,
                "metrics": self.metrics.copy(),
                "timestamp": datetime.now().isoformat()
            },
            "baseline_analysis": baseline_report,
            "recommendations": self._generate_recommendations(baseline_report)
        }
        
        logger.info("性能报告生成完成")
        
        return report
    
    def get_baseline_stats(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """获取基线统计信息
        
        Args:
            metric_name: 指标名称
            
        Returns:
            统计信息
        """
        return self.baseline.get_baseline_stats(metric_name)
    
    def reset_baselines(self, metric_name: Optional[str] = None) -> None:
        """重置基线数据
        
        Args:
            metric_name: 指定重置的指标名称，None表示重置所有
        """
        self.baseline.reset_baselines(metric_name)
        logger.info("基线数据已重置", metric_name=metric_name)
    
    async def _start_dashboard(self) -> None:
        """启动仪表板"""
        try:
            await self.dashboard.start()
            logger.info("可观测性仪表板已启动")
        except Exception as e:
            logger.error("启动仪表板失败", error=str(e))
    
    def _generate_recommendations(self, baseline_report: Dict[str, Any]) -> List[str]:
        """生成性能优化建议
        
        Args:
            baseline_report: 基线报告
            
        Returns:
            建议列表
        """
        try:
            # 使用分析引擎生成智能建议
            analysis_result = self.analysis_engine.analyze_performance_data(self.metrics)
            
            # 获取基础建议
            basic_recommendations = self._generate_basic_recommendations(baseline_report)
            
            # 合并智能分析建议
            all_recommendations = basic_recommendations + analysis_result.get('recommendations', [])
            
            # 记录到仪表板
            self.dashboard.record_metric('recommendations_generated', len(all_recommendations))
            
            logger.info("生成性能优化建议", 
                       basic_count=len(basic_recommendations),
                       intelligent_count=len(analysis_result.get('recommendations', [])),
                       total_count=len(all_recommendations))
            
            return all_recommendations
            
        except Exception as e:
            logger.error("生成优化建议失败", error=str(e))
            self.dashboard.increment_counter('recommendation_errors')
            return self._generate_basic_recommendations(baseline_report)
    
    def _generate_basic_recommendations(self, baseline_report: Dict[str, Any]) -> List[str]:
        """生成基础性能优化建议
        
        Args:
            baseline_report: 基线报告
            
        Returns:
            基础建议列表
        """
        recommendations = []
        
        summary = baseline_report.get("summary", {})
        worse_count = summary.get("worse_count", 0)
        
        if worse_count > 0:
            recommendations.append(f"发现 {worse_count} 个性能下降的指标，建议进行优化")
        
        # 分析具体指标
        metrics = baseline_report.get("metrics", {})
        for metric_name, metric_data in metrics.items():
            comparison = metric_data.get("comparison", {})
            if comparison.get("result") == "worse":
                diff = comparison.get("difference_percentage", 0)
                if diff > 20:
                    recommendations.append(f"{metric_name} 性能下降 {diff:.1f}%，需要重点关注")
                elif "load_time" in metric_name:
                    recommendations.append("页面加载时间增加，建议检查网络请求和资源大小")
                elif "action" in metric_name:
                    recommendations.append("用户操作响应时间增加，建议检查JavaScript执行效率")
        
        if not recommendations:
            recommendations.append("性能表现良好，继续保持")
        
        return recommendations
    
    async def suggest_optimizations(self, data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """生成性能优化建议
        
        基于收集的性能指标数据，生成可操作的优化建议。
        
        Args:
            data: 可选的指标数据，如果为Null则使用当前服务中收集的数据
            
        Returns:
            优化建议列表，每个建议包含特定实施操作
        """
        try:
            # 使用当前指标数据或传入的数据
            analysis_data = data or self.metrics
            if not analysis_data:
                logger.warning("没有可用的性能数据进行分析")
                return []
            
            # 调用分析引擎进行分析
            analysis_result = self.analysis_engine.analyze_performance_data(analysis_data)
            
            # 获取背景指标和趋势
            bottlenecks = analysis_result.get('bottlenecks', [])
            trends = analysis_result.get('trends', [])
            anomalies = analysis_result.get('anomalies', [])
            
            # 生成优化建议
            suggestions = self.analysis_engine.generate_optimization_suggestions(
                bottlenecks, trends, anomalies
            )
            
            # 转换成可序列化的字典格式
            serializable_suggestions = []
            for suggestion in suggestions:
                suggestion_dict = {
                    "title": suggestion.title,
                    "description": suggestion.description,
                    "category": suggestion.category,
                    "priority": suggestion.priority,
                    "estimated_impact": suggestion.estimated_impact,
                    "implementation_effort": suggestion.implementation_effort,
                    "related_metrics": suggestion.related_metrics,
                    "action_items": suggestion.action_items,
                    "confidence": suggestion.confidence
                }
                serializable_suggestions.append(suggestion_dict)
            
            # 记录到仪表盘
            self.dashboard.record_metric('suggestions_generated', len(serializable_suggestions))
            
            logger.info("生成性能优化建议", 
                       count=len(serializable_suggestions),
                       categories=set(s.get("category") for s in serializable_suggestions))
            
            return serializable_suggestions
        
        except Exception as e:
            logger.error("生成优化建议失败", error=str(e))
            return []
    
    async def auto_optimize_timeouts(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """自动优化超时设置
        
        基于性能数据自动调整超时设置，通过自动化引擎实施优化。
        
        Args:
            data: 可选的指标数据，如果为Null则使用当前服务中收集的数据
            
        Returns:
            优化结果字典
        """
        try:
            # 使用当前指标数据或传入的数据
            performance_data = data or self.metrics
            if not performance_data:
                logger.warning("没有可用的性能数据进行超时优化")
                return {"success": False, "message": "无效的性能数据"}
            
            # 分析数据并识别需要优化的超时设置
            timeout_optimizations = []
            
            # 检查页面加载指标
            if "page_loads" in performance_data:
                page_loads = performance_data["page_loads"]
                for page_load in page_loads:
                    url = page_load.get("url", "")
                    load_time = page_load.get("load_time_ms", 0)
                    if load_time > 10000:  # 如果加载时间超过10秒
                        timeout_optimizations.append({
                            "metric_name": f"load_time_{Path(url).name}", 
                            "current_value": load_time,
                            "target_improvement": 20
                        })
            
            # 检查操作响应时间
            if "actions" in performance_data:
                actions = performance_data["actions"]
                for action in actions:
                    action_name = action.get("action_name", "")
                    execution_time = action.get("execution_time_ms", 0)
                    if execution_time > 5000:  # 如果操作响应时间超过5秒
                        timeout_optimizations.append({
                            "metric_name": f"action_time_{action_name}", 
                            "current_value": execution_time,
                            "target_improvement": 30
                        })
            
            # 检查网络请求时间
            if "network" in performance_data:
                requests = performance_data["network"].get("requests", [])
                for request in requests:
                    url = request.get("url", "")
                    response_time = request.get("response_time_ms", 0)
                    if response_time > 2000:  # 如果响应时间超过2秒
                        timeout_optimizations.append({
                            "metric_name": f"response_time_{Path(url).name}", 
                            "current_value": response_time,
                            "target_improvement": 25
                        })
            
            # 添加默认超时优化项，确保至少有一个优化项
            if not timeout_optimizations:
                # 如果没有特定超时需要调整，使用通用优化
                timeout_optimizations.append({
                    "metric_name": "default_timeout", 
                    "current_value": 10000,  # 默认值
                    "target_improvement": 15
                })
            
            # 创建并执行优化任务
            optimization_results = []
            for optimization in timeout_optimizations:
                # 创建一个优化任务
                task = self.automation_engine.create_optimization_task(
                    task_type="adjust_timeout_settings",
                    parameters=optimization,
                    severity="medium",
                    auto_apply=True  # 自动应用优化
                )
                
                # 等待任务执行完成
                result = await self.automation_engine.execute_task(task.id)
                optimization_results.append(result)
            
            # 记录到仪表盘
            self.dashboard.increment_counter('timeout_optimizations', len(optimization_results))
            success_count = sum(1 for r in optimization_results if r.get("success", False))
            self.dashboard.record_metric('optimization_success_rate', success_count / len(optimization_results) if optimization_results else 0)
            
            # 汇总结果
            overall_success = all(r.get("success", False) for r in optimization_results)
            
            logger.info("超时设置自动优化完成",
                     total=len(optimization_results),
                     success=success_count,
                     overall_success=overall_success)
            
            return {
                "success": overall_success,
                "message": f"共{len(optimization_results)}个超时设置进行了优化，成功{success_count}个",
                "optimizations": optimization_results
            }
            
        except Exception as e:
            logger.error("超时设置自动优化失败", error=str(e))
            return {"success": False, "message": f"优化失败: {str(e)}"}