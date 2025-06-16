"""性能分析引擎

提供智能化的性能数据分析功能，包括：
- 性能瓶颈识别
- 趋势分析
- 异常检测
- 根因分析
- 智能优化建议生成
"""

import statistics
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional

import structlog

logger = structlog.get_logger(__name__)

class BottleneckType(Enum):
    """性能瓶颈类型"""
    NETWORK = "network"
    RENDERING = "rendering"
    JAVASCRIPT = "javascript"
    RESOURCE_LOADING = "resource_loading"
    DOM_PROCESSING = "dom_processing"
    USER_INTERACTION = "user_interaction"
    MEMORY = "memory"
    UNKNOWN = "unknown"

class SeverityLevel(Enum):
    """严重程度级别"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class Bottleneck:
    """性能瓶颈数据结构"""
    type: BottleneckType
    metric_name: str
    current_value: float
    baseline_value: float
    difference_percentage: float
    severity: SeverityLevel
    description: str
    affected_metrics: List[str]
    root_cause: Optional[str] = None
    confidence: float = 0.0

@dataclass
class TrendAnalysis:
    """趋势分析结果"""
    metric_name: str
    trend_direction: str  # "improving", "degrading", "stable"
    trend_strength: float  # 0-1, 趋势强度
    recent_change_percentage: float
    prediction: Optional[float] = None
    confidence: float = 0.0

@dataclass
class OptimizationSuggestion:
    """优化建议"""
    title: str
    description: str
    category: str
    priority: SeverityLevel
    estimated_impact: str
    implementation_effort: str
    related_metrics: List[str]
    action_items: List[str]
    confidence: float = 0.0

class PerformanceAnalysisEngine:
    """性能分析引擎
    
    提供智能化的性能数据分析和优化建议生成功能。
    """
    
    def __init__(self):
        """初始化分析引擎"""
        self.metric_thresholds = {
            # 页面加载相关阈值 (毫秒)
            "load_time_ms": {"good": 2000, "needs_improvement": 4000},
            "dom_ready_ms": {"good": 1500, "needs_improvement": 3000},
            "response_time_ms": {"good": 500, "needs_improvement": 1000},
            
            # Web Vitals阈值
            "lcp": {"good": 2500, "needs_improvement": 4000},
            "fid": {"good": 100, "needs_improvement": 300},
            "cls": {"good": 0.1, "needs_improvement": 0.25},
            "fcp": {"good": 1800, "needs_improvement": 3000},
            
            # 操作响应时间阈值
            "action_time_ms": {"good": 200, "needs_improvement": 500},
            
            # 资源相关阈值
            "resource_count": {"good": 50, "needs_improvement": 100},
            "total_size_bytes": {"good": 1024*1024, "needs_improvement": 3*1024*1024},  # 1MB, 3MB
        }
        
        logger.info("性能分析引擎初始化完成")
    
    def analyze_performance_data(self, 
                               current_metrics: Dict[str, Any],
                               baseline_data: Dict[str, Any],
                               historical_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """分析性能数据
        
        Args:
            current_metrics: 当前性能指标
            baseline_data: 基线数据
            historical_data: 历史数据
            
        Returns:
            分析结果
        """
        logger.info("开始性能数据分析")
        
        # 识别性能瓶颈
        bottlenecks = self.identify_bottlenecks(current_metrics, baseline_data)
        
        # 趋势分析
        trends = []
        if historical_data:
            trends = self.analyze_trends(historical_data)
        
        # 异常检测
        anomalies = self.detect_anomalies(current_metrics, baseline_data)
        
        # 根因分析
        root_causes = self.analyze_root_causes(bottlenecks, current_metrics)
        
        # 生成优化建议
        suggestions = self.generate_optimization_suggestions(bottlenecks, trends, anomalies)
        
        analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "bottlenecks": [self._bottleneck_to_dict(b) for b in bottlenecks],
            "trends": [self._trend_to_dict(t) for t in trends],
            "anomalies": anomalies,
            "root_causes": root_causes,
            "suggestions": [self._suggestion_to_dict(s) for s in suggestions],
            "summary": self._generate_analysis_summary(bottlenecks, trends, suggestions)
        }
        
        logger.info("性能数据分析完成", 
                   bottlenecks_count=len(bottlenecks),
                   suggestions_count=len(suggestions))
        
        return analysis_result
    
    def identify_bottlenecks(self, 
                           current_metrics: Dict[str, Any],
                           baseline_data: Dict[str, Any]) -> List[Bottleneck]:
        """识别性能瓶颈
        
        Args:
            current_metrics: 当前指标
            baseline_data: 基线数据
            
        Returns:
            瓶颈列表
        """
        bottlenecks = []
        
        # 分析页面加载指标
        page_load_metrics = current_metrics.get("page_load", {})
        if page_load_metrics:
            bottlenecks.extend(self._analyze_page_load_bottlenecks(page_load_metrics, baseline_data))
        
        # 分析Web Vitals指标
        web_vitals = current_metrics.get("web_vitals", {})
        if web_vitals:
            bottlenecks.extend(self._analyze_web_vitals_bottlenecks(web_vitals, baseline_data))
        
        # 分析用户操作指标
        actions = current_metrics.get("actions", [])
        if actions:
            bottlenecks.extend(self._analyze_action_bottlenecks(actions, baseline_data))
        
        # 按严重程度排序
        bottlenecks.sort(key=lambda x: self._severity_to_priority(x.severity))
        
        return bottlenecks
    
    def _analyze_page_load_bottlenecks(self, 
                                     page_metrics: Dict[str, Any],
                                     baseline_data: Dict[str, Any]) -> List[Bottleneck]:
        """分析页面加载瓶颈"""
        bottlenecks = []
        
        # 检查关键指标
        critical_metrics = [
            ("load_time_ms", BottleneckType.NETWORK),
            ("dom_ready_ms", BottleneckType.DOM_PROCESSING),
            ("response_time_ms", BottleneckType.NETWORK),
            ("slowest_resource_ms", BottleneckType.RESOURCE_LOADING)
        ]
        
        for metric_name, bottleneck_type in critical_metrics:
            current_value = page_metrics.get(metric_name)
            if current_value is None:
                continue
            
            # 获取基线值
            baseline_stats = baseline_data.get("metrics", {}).get(metric_name, {})
            baseline_value = baseline_stats.get("mean")
            
            if baseline_value is None:
                # 没有基线数据，使用阈值判断
                threshold = self.metric_thresholds.get(metric_name, {})
                if current_value > threshold.get("needs_improvement", float('inf')):
                    severity = SeverityLevel.HIGH
                elif current_value > threshold.get("good", 0):
                    severity = SeverityLevel.MEDIUM
                else:
                    continue
                
                bottleneck = Bottleneck(
                    type=bottleneck_type,
                    metric_name=metric_name,
                    current_value=current_value,
                    baseline_value=0,
                    difference_percentage=0,
                    severity=severity,
                    description=f"{metric_name} 超过推荐阈值",
                    affected_metrics=[metric_name],
                    confidence=0.7
                )
                bottlenecks.append(bottleneck)
            else:
                # 与基线比较
                diff_percentage = ((current_value - baseline_value) / baseline_value) * 100
                
                if diff_percentage > 20:  # 性能下降超过20%
                    severity = self._calculate_severity(diff_percentage)
                    
                    bottleneck = Bottleneck(
                        type=bottleneck_type,
                        metric_name=metric_name,
                        current_value=current_value,
                        baseline_value=baseline_value,
                        difference_percentage=diff_percentage,
                        severity=severity,
                        description=f"{metric_name} 相比基线下降 {diff_percentage:.1f}%",
                        affected_metrics=[metric_name],
                        confidence=0.8
                    )
                    bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    def _analyze_web_vitals_bottlenecks(self, 
                                      web_vitals: Dict[str, Any],
                                      baseline_data: Dict[str, Any]) -> List[Bottleneck]:
        """分析Web Vitals瓶颈"""
        bottlenecks = []
        
        vitals_mapping = {
            "lcp": (BottleneckType.RENDERING, "Largest Contentful Paint"),
            "fid": (BottleneckType.JAVASCRIPT, "First Input Delay"),
            "cls": (BottleneckType.RENDERING, "Cumulative Layout Shift"),
            "fcp": (BottleneckType.RENDERING, "First Contentful Paint")
        }
        
        for vital_name, (bottleneck_type, description) in vitals_mapping.items():
            current_value = web_vitals.get(vital_name)
            if current_value is None:
                continue
            
            threshold = self.metric_thresholds.get(vital_name, {})
            
            if current_value > threshold.get("needs_improvement", float('inf')):
                severity = SeverityLevel.HIGH
            elif current_value > threshold.get("good", 0):
                severity = SeverityLevel.MEDIUM
            else:
                continue
            
            bottleneck = Bottleneck(
                type=bottleneck_type,
                metric_name=vital_name,
                current_value=current_value,
                baseline_value=threshold.get("good", 0),
                difference_percentage=0,
                severity=severity,
                description=f"{description} 需要改进",
                affected_metrics=[vital_name],
                confidence=0.9
            )
            bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    def _analyze_action_bottlenecks(self, 
                                  actions: List[Dict[str, Any]],
                                  baseline_data: Dict[str, Any]) -> List[Bottleneck]:
        """分析用户操作瓶颈"""
        bottlenecks = []
        
        for action in actions:
            if not action.get("success", True):
                continue
            
            execution_time = action.get("execution_time_ms")
            action_name = action.get("action_name")
            
            if execution_time is None or action_name is None:
                continue
            
            # 检查是否超过阈值
            threshold = self.metric_thresholds.get("action_time_ms", {})
            
            if execution_time > threshold.get("needs_improvement", 500):
                severity = SeverityLevel.HIGH if execution_time > 1000 else SeverityLevel.MEDIUM
                
                bottleneck = Bottleneck(
                    type=BottleneckType.USER_INTERACTION,
                    metric_name=f"action_{action_name}_time",
                    current_value=execution_time,
                    baseline_value=threshold.get("good", 200),
                    difference_percentage=0,
                    severity=severity,
                    description=f"操作 '{action_name}' 响应时间过长",
                    affected_metrics=[f"action_{action_name}_time"],
                    confidence=0.8
                )
                bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    def analyze_trends(self, historical_data: List[Dict[str, Any]]) -> List[TrendAnalysis]:
        """分析性能趋势
        
        Args:
            historical_data: 历史数据列表
            
        Returns:
            趋势分析结果列表
        """
        if len(historical_data) < 3:
            return []
        
        trends = []
        
        # 提取关键指标的时间序列数据
        metric_series = self._extract_metric_series(historical_data)
        
        for metric_name, values in metric_series.items():
            if len(values) < 3:
                continue
            
            trend = self._calculate_trend(metric_name, values)
            if trend:
                trends.append(trend)
        
        return trends
    
    def _extract_metric_series(self, historical_data: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """从历史数据中提取指标时间序列"""
        metric_series = {}
        
        for data_point in historical_data:
            metrics = data_point.get("metrics", {})
            
            # 页面加载指标
            page_load = metrics.get("page_load", {})
            for key, value in page_load.items():
                if isinstance(value, (int, float)):
                    if key not in metric_series:
                        metric_series[key] = []
                    metric_series[key].append(value)
            
            # Web Vitals指标
            web_vitals = metrics.get("web_vitals", {})
            for key, value in web_vitals.items():
                if isinstance(value, (int, float)):
                    if key not in metric_series:
                        metric_series[key] = []
                    metric_series[key].append(value)
        
        return metric_series
    
    def _calculate_trend(self, metric_name: str, values: List[float]) -> Optional[TrendAnalysis]:
        """计算单个指标的趋势"""
        if len(values) < 3:
            return None
        
        # 计算线性回归斜率
        n = len(values)
        x = list(range(n))
        
        # 计算斜率
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return None
        
        slope = numerator / denominator
        
        # 确定趋势方向和强度
        if abs(slope) < 0.1:  # 相对稳定
            trend_direction = "stable"
            trend_strength = 0.0
        elif slope > 0:
            trend_direction = "degrading"  # 对于性能指标，增加通常意味着变差
            trend_strength = min(abs(slope) / y_mean, 1.0)
        else:
            trend_direction = "improving"
            trend_strength = min(abs(slope) / y_mean, 1.0)
        
        # 计算最近变化百分比
        recent_change = ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0
        
        return TrendAnalysis(
            metric_name=metric_name,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            recent_change_percentage=recent_change,
            confidence=min(trend_strength * 2, 1.0)
        )
    
    def detect_anomalies(self, 
                        current_metrics: Dict[str, Any],
                        baseline_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检测性能异常
        
        Args:
            current_metrics: 当前指标
            baseline_data: 基线数据
            
        Returns:
            异常列表
        """
        anomalies = []
        
        baseline_metrics = baseline_data.get("metrics", {})
        
        # 检查页面加载异常
        page_load = current_metrics.get("page_load", {})
        for metric_name, current_value in page_load.items():
            if not isinstance(current_value, (int, float)):
                continue
            
            baseline_stats = baseline_metrics.get(metric_name, {})
            mean = baseline_stats.get("mean")
            std_dev = baseline_stats.get("std_dev")
            
            if mean is not None and std_dev is not None and std_dev > 0:
                # 使用3-sigma规则检测异常
                z_score = abs(current_value - mean) / std_dev
                
                if z_score > 3:  # 3-sigma异常
                    anomalies.append({
                        "metric_name": metric_name,
                        "current_value": current_value,
                        "expected_range": [mean - 2*std_dev, mean + 2*std_dev],
                        "z_score": z_score,
                        "severity": "high" if z_score > 4 else "medium",
                        "description": f"{metric_name} 出现异常值，偏离正常范围 {z_score:.1f} 个标准差"
                    })
        
        return anomalies
    
    def analyze_root_causes(self, 
                          bottlenecks: List[Bottleneck],
                          current_metrics: Dict[str, Any]) -> Dict[str, List[str]]:
        """分析根因
        
        Args:
            bottlenecks: 瓶颈列表
            current_metrics: 当前指标
            
        Returns:
            根因分析结果
        """
        root_causes = {}
        
        for bottleneck in bottlenecks:
            causes = []
            
            if bottleneck.type == BottleneckType.NETWORK:
                causes.extend([
                    "网络连接质量差",
                    "服务器响应时间长",
                    "DNS解析慢",
                    "CDN配置问题"
                ])
            
            elif bottleneck.type == BottleneckType.RESOURCE_LOADING:
                page_load = current_metrics.get("page_load", {})
                resource_count = page_load.get("resource_count", 0)
                total_size = page_load.get("total_size_bytes", 0)
                
                if resource_count > 100:
                    causes.append("资源文件数量过多")
                if total_size > 3 * 1024 * 1024:  # 3MB
                    causes.append("资源文件总大小过大")
                
                causes.extend([
                    "图片未优化",
                    "JavaScript/CSS文件未压缩",
                    "缺少资源缓存策略"
                ])
            
            elif bottleneck.type == BottleneckType.RENDERING:
                causes.extend([
                    "DOM结构复杂",
                    "CSS选择器效率低",
                    "频繁的重排重绘",
                    "大量的DOM操作"
                ])
            
            elif bottleneck.type == BottleneckType.JAVASCRIPT:
                causes.extend([
                    "JavaScript执行时间长",
                    "主线程阻塞",
                    "内存泄漏",
                    "未优化的算法"
                ])
            
            elif bottleneck.type == BottleneckType.USER_INTERACTION:
                causes.extend([
                    "事件处理函数复杂",
                    "UI更新频繁",
                    "缺少防抖/节流机制",
                    "同步操作阻塞"
                ])
            
            root_causes[bottleneck.metric_name] = causes
        
        return root_causes
    
    def generate_optimization_suggestions(self, 
                                        bottlenecks: List[Bottleneck],
                                        trends: List[TrendAnalysis],
                                        anomalies: List[Dict[str, Any]]) -> List[OptimizationSuggestion]:
        """生成优化建议
        
        Args:
            bottlenecks: 瓶颈列表
            trends: 趋势分析
            anomalies: 异常列表
            
        Returns:
            优化建议列表
        """
        suggestions = []
        
        # 基于瓶颈生成建议
        for bottleneck in bottlenecks:
            suggestion = self._generate_bottleneck_suggestion(bottleneck)
            if suggestion:
                suggestions.append(suggestion)
        
        # 基于趋势生成建议
        for trend in trends:
            if trend.trend_direction == "degrading" and trend.trend_strength > 0.3:
                suggestion = self._generate_trend_suggestion(trend)
                if suggestion:
                    suggestions.append(suggestion)
        
        # 基于异常生成建议
        for anomaly in anomalies:
            suggestion = self._generate_anomaly_suggestion(anomaly)
            if suggestion:
                suggestions.append(suggestion)
        
        # 去重和排序
        suggestions = self._deduplicate_suggestions(suggestions)
        suggestions.sort(key=lambda x: self._severity_to_priority(x.priority))
        
        return suggestions
    
    def _generate_bottleneck_suggestion(self, bottleneck: Bottleneck) -> Optional[OptimizationSuggestion]:
        """基于瓶颈生成优化建议"""
        if bottleneck.type == BottleneckType.NETWORK:
            return OptimizationSuggestion(
                title="网络性能优化",
                description=f"检测到网络相关性能瓶颈：{bottleneck.description}",
                category="网络优化",
                priority=bottleneck.severity,
                estimated_impact="高",
                implementation_effort="中等",
                related_metrics=[bottleneck.metric_name],
                action_items=[
                    "检查服务器响应时间",
                    "优化DNS解析",
                    "启用CDN加速",
                    "使用HTTP/2协议",
                    "启用Gzip压缩"
                ],
                confidence=bottleneck.confidence
            )
        
        elif bottleneck.type == BottleneckType.RESOURCE_LOADING:
            return OptimizationSuggestion(
                title="资源加载优化",
                description=f"检测到资源加载性能瓶颈：{bottleneck.description}",
                category="资源优化",
                priority=bottleneck.severity,
                estimated_impact="高",
                implementation_effort="中等",
                related_metrics=[bottleneck.metric_name],
                action_items=[
                    "压缩图片和静态资源",
                    "合并CSS和JavaScript文件",
                    "实施资源懒加载",
                    "优化资源缓存策略",
                    "使用WebP格式图片"
                ],
                confidence=bottleneck.confidence
            )
        
        elif bottleneck.type == BottleneckType.RENDERING:
            return OptimizationSuggestion(
                title="渲染性能优化",
                description=f"检测到渲染性能瓶颈：{bottleneck.description}",
                category="渲染优化",
                priority=bottleneck.severity,
                estimated_impact="中等",
                implementation_effort="高",
                related_metrics=[bottleneck.metric_name],
                action_items=[
                    "优化CSS选择器",
                    "减少DOM复杂度",
                    "避免强制同步布局",
                    "使用CSS transform代替位置变化",
                    "实施虚拟滚动"
                ],
                confidence=bottleneck.confidence
            )
        
        elif bottleneck.type == BottleneckType.JAVASCRIPT:
            return OptimizationSuggestion(
                title="JavaScript性能优化",
                description=f"检测到JavaScript性能瓶颈：{bottleneck.description}",
                category="脚本优化",
                priority=bottleneck.severity,
                estimated_impact="高",
                implementation_effort="中等",
                related_metrics=[bottleneck.metric_name],
                action_items=[
                    "优化JavaScript执行效率",
                    "使用Web Workers处理复杂计算",
                    "实施代码分割",
                    "移除未使用的代码",
                    "使用requestAnimationFrame优化动画"
                ],
                confidence=bottleneck.confidence
            )
        
        elif bottleneck.type == BottleneckType.USER_INTERACTION:
            return OptimizationSuggestion(
                title="交互响应优化",
                description=f"检测到用户交互性能瓶颈：{bottleneck.description}",
                category="交互优化",
                priority=bottleneck.severity,
                estimated_impact="中等",
                implementation_effort="低",
                related_metrics=[bottleneck.metric_name],
                action_items=[
                    "实施事件防抖和节流",
                    "优化事件处理函数",
                    "使用异步操作",
                    "减少UI更新频率",
                    "实施虚拟化技术"
                ],
                confidence=bottleneck.confidence
            )
        
        return None
    
    def _generate_trend_suggestion(self, trend: TrendAnalysis) -> Optional[OptimizationSuggestion]:
        """基于趋势生成优化建议"""
        if trend.trend_direction == "degrading":
            return OptimizationSuggestion(
                title=f"性能趋势预警 - {trend.metric_name}",
                description=f"检测到 {trend.metric_name} 呈现下降趋势，变化幅度 {trend.recent_change_percentage:.1f}%",
                category="趋势预警",
                priority=SeverityLevel.MEDIUM,
                estimated_impact="中等",
                implementation_effort="低",
                related_metrics=[trend.metric_name],
                action_items=[
                    "监控性能趋势变化",
                    "分析最近的代码变更",
                    "检查系统资源使用情况",
                    "进行性能回归测试"
                ],
                confidence=trend.confidence
            )
        
        return None
    
    def _generate_anomaly_suggestion(self, anomaly: Dict[str, Any]) -> Optional[OptimizationSuggestion]:
        """基于异常生成优化建议"""
        return OptimizationSuggestion(
            title=f"性能异常处理 - {anomaly['metric_name']}",
            description=anomaly['description'],
            category="异常处理",
            priority=SeverityLevel.HIGH if anomaly['severity'] == 'high' else SeverityLevel.MEDIUM,
            estimated_impact="高",
            implementation_effort="低",
            related_metrics=[anomaly['metric_name']],
            action_items=[
                "立即检查系统状态",
                "分析异常发生时间点",
                "检查相关日志",
                "验证数据准确性"
            ],
            confidence=0.9
        )
    
    def _deduplicate_suggestions(self, suggestions: List[OptimizationSuggestion]) -> List[OptimizationSuggestion]:
        """去除重复的优化建议"""
        seen_titles = set()
        unique_suggestions = []
        
        for suggestion in suggestions:
            if suggestion.title not in seen_titles:
                seen_titles.add(suggestion.title)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions
    
    def _calculate_severity(self, difference_percentage: float) -> SeverityLevel:
        """根据差异百分比计算严重程度"""
        if difference_percentage > 100:
            return SeverityLevel.CRITICAL
        elif difference_percentage > 50:
            return SeverityLevel.HIGH
        elif difference_percentage > 20:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _severity_to_priority(self, severity: SeverityLevel) -> int:
        """将严重程度转换为优先级数字"""
        priority_map = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 3,
            SeverityLevel.INFO: 4
        }
        return priority_map.get(severity, 5)
    
    def _bottleneck_to_dict(self, bottleneck: Bottleneck) -> Dict[str, Any]:
        """将瓶颈对象转换为字典"""
        return {
            "type": bottleneck.type.value,
            "metric_name": bottleneck.metric_name,
            "current_value": bottleneck.current_value,
            "baseline_value": bottleneck.baseline_value,
            "difference_percentage": bottleneck.difference_percentage,
            "severity": bottleneck.severity.value,
            "description": bottleneck.description,
            "affected_metrics": bottleneck.affected_metrics,
            "root_cause": bottleneck.root_cause,
            "confidence": bottleneck.confidence
        }
    
    def _trend_to_dict(self, trend: TrendAnalysis) -> Dict[str, Any]:
        """将趋势对象转换为字典"""
        return {
            "metric_name": trend.metric_name,
            "trend_direction": trend.trend_direction,
            "trend_strength": trend.trend_strength,
            "recent_change_percentage": trend.recent_change_percentage,
            "prediction": trend.prediction,
            "confidence": trend.confidence
        }
    
    def _suggestion_to_dict(self, suggestion: OptimizationSuggestion) -> Dict[str, Any]:
        """将建议对象转换为字典"""
        return {
            "title": suggestion.title,
            "description": suggestion.description,
            "category": suggestion.category,
            "priority": suggestion.priority.value,
            "estimated_impact": suggestion.estimated_impact,
            "implementation_effort": suggestion.implementation_effort,
            "related_metrics": suggestion.related_metrics,
            "action_items": suggestion.action_items,
            "confidence": suggestion.confidence
        }
    
    def _generate_analysis_summary(self, 
                                 bottlenecks: List[Bottleneck],
                                 trends: List[TrendAnalysis],
                                 suggestions: List[OptimizationSuggestion]) -> Dict[str, Any]:
        """生成分析摘要"""
        # 统计瓶颈严重程度
        severity_counts = {}
        for bottleneck in bottlenecks:
            severity = bottleneck.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # 统计趋势方向
        trend_counts = {}
        for trend in trends:
            direction = trend.trend_direction
            trend_counts[direction] = trend_counts.get(direction, 0) + 1
        
        # 计算总体健康评分 (0-100)
        health_score = 100
        
        # 根据瓶颈扣分
        for bottleneck in bottlenecks:
            if bottleneck.severity == SeverityLevel.CRITICAL:
                health_score -= 20
            elif bottleneck.severity == SeverityLevel.HIGH:
                health_score -= 10
            elif bottleneck.severity == SeverityLevel.MEDIUM:
                health_score -= 5
        
        # 根据下降趋势扣分
        degrading_trends = [t for t in trends if t.trend_direction == "degrading"]
        health_score -= len(degrading_trends) * 5
        
        health_score = max(0, health_score)
        
        return {
            "health_score": health_score,
            "total_bottlenecks": len(bottlenecks),
            "severity_distribution": severity_counts,
            "trend_distribution": trend_counts,
            "total_suggestions": len(suggestions),
            "priority_suggestions": len([s for s in suggestions if s.priority in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]]),
            "overall_status": self._get_overall_status(health_score)
        }
    
    def _get_overall_status(self, health_score: int) -> str:
        """根据健康评分获取总体状态"""
        if health_score >= 90:
            return "excellent"
        elif health_score >= 75:
            return "good"
        elif health_score >= 60:
            return "fair"
        elif health_score >= 40:
            return "poor"
        else:
            return "critical"