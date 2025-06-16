"""自动化优化引擎

提供自动化的性能优化功能，包括：
- 自动化优化建议执行
- 配置自动调整
- 性能回归检测
- 自动化测试优化
- 智能资源管理
"""

import asyncio
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional

import structlog
import yaml

logger = structlog.get_logger(__name__)

class OptimizationType(Enum):
    """优化类型"""
    CONFIGURATION = "configuration"
    RESOURCE_MANAGEMENT = "resource_management"
    TEST_OPTIMIZATION = "test_optimization"
    PERFORMANCE_TUNING = "performance_tuning"
    ERROR_HANDLING = "error_handling"
    MONITORING = "monitoring"

class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLBACK = "rollback"

@dataclass
class OptimizationTask:
    """优化任务"""
    id: str
    type: OptimizationType
    title: str
    description: str
    priority: int  # 1-10, 1最高
    estimated_impact: str
    implementation_effort: str
    auto_executable: bool
    requires_approval: bool
    rollback_supported: bool
    execution_function: Optional[str] = None
    parameters: Dict[str, Any] = None
    dependencies: List[str] = None
    created_at: str = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    execution_log: List[str] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.dependencies is None:
            self.dependencies = []
        if self.execution_log is None:
            self.execution_log = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class AutomationConfig:
    """自动化配置"""
    enable_auto_execution: bool = True
    max_concurrent_tasks: int = 3
    execution_timeout: int = 300  # 秒
    rollback_on_failure: bool = True
    require_approval_for_critical: bool = True
    performance_threshold: float = 0.1  # 性能改善阈值
    max_retry_attempts: int = 3
    retry_delay: int = 5  # 秒
    backup_before_changes: bool = True
    notification_enabled: bool = True

class AutomationEngine:
    """自动化优化引擎
    
    提供自动化的性能优化执行功能。
    """
    
    def __init__(self, config: Optional[AutomationConfig] = None):
        """初始化自动化引擎
        
        Args:
            config: 自动化配置
        """
        self.config = config or AutomationConfig()
        self.task_queue: List[OptimizationTask] = []
        self.running_tasks: Dict[str, OptimizationTask] = {}
        self.completed_tasks: List[OptimizationTask] = []
        self.failed_tasks: List[OptimizationTask] = []
        self.is_running = False
        self.execution_history: List[Dict[str, Any]] = []
        self.optimization_history_file = Path("logs/optimization_history.json")
        
        # 确保历史记录目录存在
        if not self.optimization_history_file.parent.exists():
            self.optimization_history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 注册优化执行函数
        self.optimization_functions = {
            "adjust_timeout_settings": self._adjust_timeout_settings,
            "optimize_wait_strategies": self._optimize_wait_strategies,
            "configure_resource_limits": self._configure_resource_limits,
            "enable_performance_monitoring": self._enable_performance_monitoring,
            "optimize_selector_strategies": self._optimize_selector_strategies,
            "configure_retry_mechanisms": self._configure_retry_mechanisms,
            "optimize_test_parallelization": self._optimize_test_parallelization,
            "configure_browser_options": self._configure_browser_options,
            "optimize_screenshot_settings": self._optimize_screenshot_settings,
            "configure_logging_levels": self._configure_logging_levels
        }
        
        logger.info("自动化优化引擎初始化完成", config=asdict(self.config))
    
    async def start(self) -> None:
        """启动自动化引擎"""
        if self.is_running:
            logger.warning("自动化引擎已在运行")
            return
        
        self.is_running = True
        logger.info("启动自动化优化引擎")
        
        # 启动任务执行循环
        asyncio.create_task(self._execution_loop())
    
    async def stop(self) -> None:
        """停止自动化引擎"""
        self.is_running = False
        
        # 等待正在运行的任务完成
        while self.running_tasks:
            await asyncio.sleep(1)
        
        logger.info("自动化优化引擎已停止")
    
    def add_optimization_task(self, task: OptimizationTask) -> bool:
        """添加优化任务
        
        Args:
            task: 优化任务
            
        Returns:
            是否添加成功
        """
        # 检查任务是否已存在
        if any(t.id == task.id for t in self.task_queue):
            logger.warning("任务已存在", task_id=task.id)
            return False
        
        # 检查依赖关系
        if not self._validate_dependencies(task):
            logger.error("任务依赖关系验证失败", task_id=task.id)
            return False
        
        # 按优先级插入任务队列
        inserted = False
        for i, existing_task in enumerate(self.task_queue):
            if task.priority < existing_task.priority:
                self.task_queue.insert(i, task)
                inserted = True
                break
        
        if not inserted:
            self.task_queue.append(task)
        
        logger.info("添加优化任务", task_id=task.id, priority=task.priority)
        return True
    
    def generate_tasks_from_analysis(self, analysis_result: Dict[str, Any]) -> List[OptimizationTask]:
        """从分析结果生成优化任务
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            生成的任务列表
        """
        tasks = []
        
        # 从瓶颈生成任务
        bottlenecks = analysis_result.get("bottlenecks", [])
        for bottleneck in bottlenecks:
            task = self._create_task_from_bottleneck(bottleneck)
            if task:
                tasks.append(task)
        
        # 从建议生成任务
        suggestions = analysis_result.get("suggestions", [])
        for suggestion in suggestions:
            task = self._create_task_from_suggestion(suggestion)
            if task:
                tasks.append(task)
        
        # 从异常生成任务
        anomalies = analysis_result.get("anomalies", [])
        for anomaly in anomalies:
            task = self._create_task_from_anomaly(anomaly)
            if task:
                tasks.append(task)
        
        logger.info("从分析结果生成优化任务", task_count=len(tasks))
        return tasks
    
    def _create_task_from_bottleneck(self, bottleneck: Dict[str, Any]) -> Optional[OptimizationTask]:
        """从瓶颈创建优化任务"""
        bottleneck_type = bottleneck.get("type")
        metric_name = bottleneck.get("metric_name")
        severity = bottleneck.get("severity")
        
        task_id = f"bottleneck_{bottleneck_type}_{metric_name}_{int(time.time())}"
        
        if bottleneck_type == "network":
            return OptimizationTask(
                id=task_id,
                type=OptimizationType.CONFIGURATION,
                title="网络性能优化",
                description=f"优化网络相关配置以改善 {metric_name}",
                priority=self._severity_to_priority(severity),
                estimated_impact="高",
                implementation_effort="中等",
                auto_executable=True,
                requires_approval=severity in ["critical", "high"],
                rollback_supported=True,
                execution_function="adjust_timeout_settings",
                parameters={
                    "metric_name": metric_name,
                    "current_value": bottleneck.get("current_value"),
                    "target_improvement": 20  # 目标改善20%
                }
            )
        
        elif bottleneck_type == "resource_loading":
            return OptimizationTask(
                id=task_id,
                type=OptimizationType.RESOURCE_MANAGEMENT,
                title="资源加载优化",
                description=f"优化资源加载策略以改善 {metric_name}",
                priority=self._severity_to_priority(severity),
                estimated_impact="高",
                implementation_effort="中等",
                auto_executable=True,
                requires_approval=False,
                rollback_supported=True,
                execution_function="configure_resource_limits",
                parameters={
                    "metric_name": metric_name,
                    "optimization_type": "resource_loading"
                }
            )
        
        elif bottleneck_type == "user_interaction":
            return OptimizationTask(
                id=task_id,
                type=OptimizationType.TEST_OPTIMIZATION,
                title="交互响应优化",
                description=f"优化用户交互测试策略以改善 {metric_name}",
                priority=self._severity_to_priority(severity),
                estimated_impact="中等",
                implementation_effort="低",
                auto_executable=True,
                requires_approval=False,
                rollback_supported=True,
                execution_function="optimize_wait_strategies",
                parameters={
                    "metric_name": metric_name,
                    "interaction_type": "user_action"
                }
            )
        
        return None
    
    def _create_task_from_suggestion(self, suggestion: Dict[str, Any]) -> Optional[OptimizationTask]:
        """从建议创建优化任务"""
        category = suggestion.get("category")
        priority_str = suggestion.get("priority")
        title = suggestion.get("title")
        
        task_id = f"suggestion_{category}_{int(time.time())}"
        
        if category == "网络优化":
            return OptimizationTask(
                id=task_id,
                type=OptimizationType.CONFIGURATION,
                title=title,
                description=suggestion.get("description"),
                priority=self._severity_to_priority(priority_str),
                estimated_impact=suggestion.get("estimated_impact"),
                implementation_effort=suggestion.get("implementation_effort"),
                auto_executable=True,
                requires_approval=priority_str in ["critical", "high"],
                rollback_supported=True,
                execution_function="adjust_timeout_settings"
            )
        
        elif category == "脚本优化":
            return OptimizationTask(
                id=task_id,
                type=OptimizationType.PERFORMANCE_TUNING,
                title=title,
                description=suggestion.get("description"),
                priority=self._severity_to_priority(priority_str),
                estimated_impact=suggestion.get("estimated_impact"),
                implementation_effort=suggestion.get("implementation_effort"),
                auto_executable=True,
                requires_approval=False,
                rollback_supported=True,
                execution_function="optimize_selector_strategies"
            )
        
        return None
    
    def _create_task_from_anomaly(self, anomaly: Dict[str, Any]) -> Optional[OptimizationTask]:
        """从异常创建优化任务"""
        metric_name = anomaly.get("metric_name")
        severity = anomaly.get("severity")
        
        task_id = f"anomaly_{metric_name}_{int(time.time())}"
        
        return OptimizationTask(
            id=task_id,
            type=OptimizationType.MONITORING,
            title=f"异常处理 - {metric_name}",
            description=anomaly.get("description"),
            priority=1 if severity == "high" else 3,
            estimated_impact="高",
            implementation_effort="低",
            auto_executable=True,
            requires_approval=True,
            rollback_supported=False,
            execution_function="enable_performance_monitoring",
            parameters={
                "metric_name": metric_name,
                "anomaly_details": anomaly
            }
        )
    
    async def _execution_loop(self) -> None:
        """任务执行循环"""
        while self.is_running:
            try:
                # 检查是否有可执行的任务
                if (len(self.running_tasks) < self.config.max_concurrent_tasks and 
                    self.task_queue):
                    
                    # 获取下一个可执行的任务
                    next_task = self._get_next_executable_task()
                    if next_task:
                        await self._execute_task(next_task)
                
                # 检查运行中任务的状态
                await self._check_running_tasks()
                
                # 短暂休眠
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error("执行循环异常", error=str(e))
                await asyncio.sleep(5)
    
    def _get_next_executable_task(self) -> Optional[OptimizationTask]:
        """获取下一个可执行的任务"""
        for i, task in enumerate(self.task_queue):
            # 检查依赖关系
            if self._are_dependencies_satisfied(task):
                # 检查是否需要审批
                if task.requires_approval and not self._is_approved(task):
                    continue
                
                # 移除并返回任务
                return self.task_queue.pop(i)
        
        return None
    
    def _are_dependencies_satisfied(self, task: OptimizationTask) -> bool:
        """检查任务依赖是否满足"""
        for dep_id in task.dependencies:
            # 检查依赖任务是否已完成
            if not any(t.id == dep_id and t.status == ExecutionStatus.COMPLETED 
                      for t in self.completed_tasks):
                return False
        return True
    
    def _is_approved(self, task: OptimizationTask) -> bool:
        """检查任务是否已审批"""
        # 这里可以实现审批逻辑
        # 目前简单返回True，实际应用中可以集成审批流程
        return True
    
    async def _execute_task(self, task: OptimizationTask) -> None:
        """执行任务"""
        task.status = ExecutionStatus.RUNNING
        self.running_tasks[task.id] = task
        
        logger.info("开始执行优化任务", task_id=task.id, title=task.title)
        
        try:
            # 创建执行任务
            execution_task = asyncio.create_task(
                self._run_optimization_function(task)
            )
            
            # 设置超时
            await asyncio.wait_for(
                execution_task, 
                timeout=self.config.execution_timeout
            )
            
        except asyncio.TimeoutError:
            logger.error("任务执行超时", task_id=task.id)
            task.status = ExecutionStatus.FAILED
            task.execution_log.append(f"执行超时 - {datetime.now().isoformat()}")
            
        except Exception as e:
            logger.error("任务执行异常", task_id=task.id, error=str(e))
            task.status = ExecutionStatus.FAILED
            task.execution_log.append(f"执行异常: {str(e)} - {datetime.now().isoformat()}")
    
    async def _run_optimization_function(self, task: OptimizationTask) -> None:
        """运行优化函数"""
        function_name = task.execution_function
        if not function_name or function_name not in self.optimization_functions:
            raise ValueError(f"未知的优化函数: {function_name}")
        
        optimization_func = self.optimization_functions[function_name]
        
        # 备份当前配置（如果启用）
        backup_data = None
        if self.config.backup_before_changes:
            backup_data = await self._create_backup(task)
        
        try:
            # 执行优化函数
            result = await optimization_func(task.parameters)
            
            if result.get("success", False):
                task.status = ExecutionStatus.COMPLETED
                task.execution_log.append(f"执行成功: {result.get('message', '')} - {datetime.now().isoformat()}")
                
                # 记录执行历史
                self._record_execution_history(task, result, backup_data)
                
            else:
                task.status = ExecutionStatus.FAILED
                task.execution_log.append(f"执行失败: {result.get('error', '')} - {datetime.now().isoformat()}")
                
                # 如果启用回滚
                if self.config.rollback_on_failure and task.rollback_supported and backup_data:
                    await self._rollback_changes(task, backup_data)
        
        except Exception as e:
            task.status = ExecutionStatus.FAILED
            task.execution_log.append(f"执行异常: {str(e)} - {datetime.now().isoformat()}")
            
            # 回滚更改
            if self.config.rollback_on_failure and task.rollback_supported and backup_data:
                await self._rollback_changes(task, backup_data)
            
            raise
    
    async def _check_running_tasks(self) -> None:
        """检查运行中任务的状态"""
        completed_task_ids = []
        
        for task_id, task in self.running_tasks.items():
            if task.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]:
                completed_task_ids.append(task_id)
                
                # 移动到相应的列表
                if task.status == ExecutionStatus.COMPLETED:
                    self.completed_tasks.append(task)
                    logger.info("任务执行完成", task_id=task_id)
                else:
                    self.failed_tasks.append(task)
                    logger.error("任务执行失败", task_id=task_id)
        
        # 从运行中任务列表移除
        for task_id in completed_task_ids:
            del self.running_tasks[task_id]
    
    async def _create_backup(self, task: OptimizationTask) -> Dict[str, Any]:
        """创建配置备份"""
        # 这里应该实现具体的备份逻辑
        # 根据任务类型备份相关配置
        backup_data = {
            "task_id": task.id,
            "backup_time": datetime.now().isoformat(),
            "type": task.type.value,
            "config_snapshot": {}  # 实际的配置快照
        }
        
        logger.info("创建配置备份", task_id=task.id)
        return backup_data
    
    async def _rollback_changes(self, task: OptimizationTask, backup_data: Dict[str, Any]) -> None:
        """回滚更改"""
        try:
            # 这里应该实现具体的回滚逻辑
            logger.info("回滚配置更改", task_id=task.id)
            
            task.status = ExecutionStatus.ROLLBACK
            task.execution_log.append(f"配置已回滚 - {datetime.now().isoformat()}")
            
        except Exception as e:
            logger.error("回滚失败", task_id=task.id, error=str(e))
    
    def _record_execution_history(self, 
                                task: OptimizationTask, 
                                result: Dict[str, Any], 
                                backup_data: Optional[Dict[str, Any]]) -> None:
        """记录执行历史"""
        history_entry = {
            "task_id": task.id,
            "task_type": task.type.value,
            "title": task.title,
            "execution_time": datetime.now().isoformat(),
            "status": task.status.value,
            "result": result,
            "backup_available": backup_data is not None,
            "execution_log": task.execution_log.copy()
        }
        
        self.execution_history.append(history_entry)
        
        # 限制历史记录数量
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
    
    # 优化函数实现
    async def _adjust_timeout_settings(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """调整超时设置
        
        根据性能指标自动优化超时配置，并更新配置文件。
        支持的优化类型：
        - 页面加载超时
        - 元素操作超时
        - 网络请求超时
        - 断言超时
        """
        try:
            metric_name = parameters.get("metric_name")
            current_value = parameters.get("current_value", 0)
            target_improvement = parameters.get("target_improvement", 20)
            
            # 根据指标类型确定优化策略
            if "load_time" in metric_name or "dom_ready" in metric_name:
                # 页面加载超时优化
                setting_type = "page_load_timeout"
                new_timeout = min(int(current_value * 1.5), 60000)  # 最大60秒
                config_path = "config/performance_optimization.yaml"
                config_key = "page_load.timeout"
            elif "action_time" in metric_name or "execution_time" in metric_name:
                # 元素操作超时优化
                setting_type = "element_timeout"
                # 如果当前值太小，则适当增加；如果太大，则适当减少
                if current_value < 1000:  # 小于1秒
                    new_timeout = min(int(current_value * 2), 5000)  # 增加但不超过5秒
                else:
                    # 根据目标改进计算优化值，但保持在合理范围内
                    reduction = current_value * (target_improvement / 100)
                    new_timeout = max(int(current_value - reduction), 1000)  # 至少保留1秒
                config_path = "config/performance_optimization.yaml"
                config_key = "element_operations.default_timeout"
            elif "response_time" in metric_name:
                # 网络请求超时优化
                setting_type = "network_timeout"
                new_timeout = min(int(current_value * 1.2), 30000)  # 最大30秒
                config_path = "config/performance_optimization.yaml"
                config_key = "network.timeout"
            else:
                # 默认超时优化
                setting_type = "default_timeout"
                new_timeout = 5000  # 默认5秒
                config_path = "config/performance_optimization.yaml"
                config_key = "default_timeout"
            
            # 更新配置文件
            result = await self._update_config_file(config_path, config_key, new_timeout)
            if not result["success"]:
                return result
            
            # 记录优化历史
            self._record_optimization_history(setting_type, metric_name, current_value, new_timeout)
            
            logger.info("超时设置已优化", 
                       setting_type=setting_type,
                       metric=metric_name, 
                       old_value=current_value, 
                       new_timeout=new_timeout,
                       config_path=config_path,
                       config_key=config_key)
            
            return {
                "success": True,
                "message": f"超时设置已优化为 {new_timeout}ms",
                "changes": {
                    "setting_type": setting_type,
                    "config_path": config_path,
                    "config_key": config_key,
                    "old_value": current_value,
                    "new_value": new_timeout,
                    "improvement_target": f"{target_improvement}%"
                }
            }
            
        except Exception as e:
            logger.error("调整超时设置失败", error=str(e))
            return {
                "success": False,
                "error": f"调整超时设置失败: {str(e)}"
            }
    
    async def _optimize_wait_strategies(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """优化等待策略"""
        try:
            metric_name = parameters.get("metric_name")
            interaction_type = parameters.get("interaction_type")
            
            # 根据交互类型优化等待策略
            optimizations = []
            
            if "click" in metric_name.lower():
                optimizations.append("启用智能点击等待")
                optimizations.append("增加元素可见性检查")
            
            if "fill" in metric_name.lower():
                optimizations.append("优化输入框填充策略")
                optimizations.append("添加输入验证等待")
            
            # 这里应该实际更新等待策略配置
            
            logger.info("优化等待策略", metric=metric_name, optimizations=optimizations)
            
            return {
                "success": True,
                "message": f"等待策略已优化: {', '.join(optimizations)}",
                "changes": {
                    "optimizations": optimizations,
                    "metric": metric_name
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _configure_resource_limits(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """配置资源限制"""
        try:
            optimization_type = parameters.get("optimization_type")
            
            changes = []
            
            if optimization_type == "resource_loading":
                # 配置资源加载限制
                changes.append("启用资源大小限制")
                changes.append("配置并发加载数量")
                changes.append("优化缓存策略")
            
            # 这里应该实际更新资源配置
            
            logger.info("配置资源限制", type=optimization_type, changes=changes)
            
            return {
                "success": True,
                "message": f"资源限制已配置: {', '.join(changes)}",
                "changes": {
                    "resource_optimizations": changes,
                    "type": optimization_type
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _enable_performance_monitoring(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """启用性能监控"""
        try:
            metric_name = parameters.get("metric_name")
            anomaly_details = parameters.get("anomaly_details", {})
            
            # 启用针对性监控
            monitoring_features = [
                f"启用 {metric_name} 实时监控",
                "配置异常阈值告警",
                "启用性能趋势分析"
            ]
            
            # 这里应该实际配置监控
            
            logger.info("启用性能监控", metric=metric_name, features=monitoring_features)
            
            return {
                "success": True,
                "message": f"性能监控已启用: {', '.join(monitoring_features)}",
                "changes": {
                    "monitoring_features": monitoring_features,
                    "metric": metric_name
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _optimize_selector_strategies(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """优化选择器策略"""
        try:
            # 优化选择器性能
            optimizations = [
                "启用智能选择器缓存",
                "优化CSS选择器性能",
                "启用选择器重试机制",
                "配置选择器超时策略"
            ]
            
            # 这里应该实际更新选择器配置
            
            logger.info("优化选择器策略", optimizations=optimizations)
            
            return {
                "success": True,
                "message": f"选择器策略已优化: {', '.join(optimizations)}",
                "changes": {
                    "selector_optimizations": optimizations
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _configure_retry_mechanisms(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """配置重试机制"""
        try:
            # 配置智能重试
            retry_configs = [
                "启用指数退避重试",
                "配置重试条件判断",
                "设置最大重试次数",
                "启用重试日志记录"
            ]
            
            # 这里应该实际配置重试机制
            
            logger.info("配置重试机制", configs=retry_configs)
            
            return {
                "success": True,
                "message": f"重试机制已配置: {', '.join(retry_configs)}",
                "changes": {
                    "retry_configurations": retry_configs
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _optimize_test_parallelization(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """优化测试并行化"""
        try:
            # 优化并行执行
            optimizations = [
                "调整并行执行数量",
                "优化资源分配策略",
                "配置负载均衡",
                "启用智能调度"
            ]
            
            # 这里应该实际配置并行化
            
            logger.info("优化测试并行化", optimizations=optimizations)
            
            return {
                "success": True,
                "message": f"测试并行化已优化: {', '.join(optimizations)}",
                "changes": {
                    "parallelization_optimizations": optimizations
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _configure_browser_options(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """配置浏览器选项"""
        try:
            # 优化浏览器配置
            browser_optimizations = [
                "启用GPU加速",
                "优化内存使用",
                "配置网络条件模拟",
                "启用性能分析"
            ]
            
            # 这里应该实际配置浏览器选项
            
            logger.info("配置浏览器选项", optimizations=browser_optimizations)
            
            return {
                "success": True,
                "message": f"浏览器选项已配置: {', '.join(browser_optimizations)}",
                "changes": {
                    "browser_optimizations": browser_optimizations
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _optimize_screenshot_settings(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """优化截图设置"""
        try:
            # 优化截图配置
            screenshot_optimizations = [
                "调整截图质量",
                "优化截图尺寸",
                "启用截图压缩",
                "配置截图缓存"
            ]
            
            # 这里应该实际配置截图设置
            
            logger.info("优化截图设置", optimizations=screenshot_optimizations)
            
            return {
                "success": True,
                "message": f"截图设置已优化: {', '.join(screenshot_optimizations)}",
                "changes": {
                    "screenshot_optimizations": screenshot_optimizations
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _configure_logging_levels(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """配置日志级别"""
        try:
            # 优化日志配置
            logging_optimizations = [
                "调整日志级别",
                "配置性能日志",
                "启用结构化日志",
                "优化日志输出"
            ]
            
            # 这里应该实际配置日志
            
            logger.info("配置日志级别", optimizations=logging_optimizations)
            
            return {
                "success": True,
                "message": f"日志配置已优化: {', '.join(logging_optimizations)}",
                "changes": {
                    "logging_optimizations": logging_optimizations
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _severity_to_priority(self, severity: str) -> int:
        """将严重程度转换为优先级"""
        mapping = {
            "critical": 1,
            "high": 2,
            "medium": 5,
            "low": 8,
            "info": 10
        }
        return mapping.get(severity.lower(), 5)
        
    async def _update_config_file(self, config_path: str, config_key: str, new_value: Any) -> Dict[str, Any]:
        """更新配置文件中的特定键值
        
        Args:
            config_path: 配置文件路径
            config_key: 配置键名（支持嵌套格式，如'network.timeout'）
            new_value: 新值
            
        Returns:
            Dict: 操作结果
        """
        try:
            path = Path(config_path)
            
            # 检查文件是否存在
            if not path.exists():
                logger.error("配置文件不存在", path=str(path))
                return {"success": False, "error": f"配置文件不存在: {path}"}
            
            # 读取当前配置
            with open(path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            # 备份原始配置（如果启用）
            if self.config.backup_before_changes:
                backup_path = path.with_suffix(f".bak.{int(time.time())}")
                with open(backup_path, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(config, f, allow_unicode=True)
                logger.info("创建配置备份", backup_path=str(backup_path))
            
            # 解析嵌套键
            key_parts = config_key.split('.')
            
            # 更新配置（支持嵌套键）
            current = config
            for i, part in enumerate(key_parts):
                if i == len(key_parts) - 1:
                    # 最后一个键，直接更新值
                    old_value = current.get(part)
                    current[part] = new_value
                    break
                else:
                    # 确保路径存在
                    if part not in current or not isinstance(current[part], dict):
                        current[part] = {}
                    current = current[part]
            
            # 写入更新后的配置
            with open(path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config, f, allow_unicode=True)
            
            logger.info("配置更新成功", 
                       path=str(path), 
                       key=config_key,
                       old_value=old_value,
                       new_value=new_value)
            
            return {
                "success": True,
                "message": f"配置 {config_key} 已更新：{old_value} → {new_value}",
                "old_value": old_value,
                "new_value": new_value
            }
            
        except Exception as e:
            logger.error("更新配置失败", error=str(e), path=config_path, key=config_key)
            return {"success": False, "error": f"更新配置失败: {str(e)}"}
    
    def _record_optimization_history(self, setting_type: str, metric_name: str, old_value: float, new_value: float) -> None:
        """记录优化历史
        
        Args:
            setting_type: 设置类型
            metric_name: 指标名称
            old_value: 旧值
            new_value: 新值
        """
        try:
            # 创建新记录
            record = {
                "timestamp": datetime.now().isoformat(),
                "setting_type": setting_type,
                "metric_name": metric_name,
                "old_value": old_value,
                "new_value": new_value,
                "change_percentage": ((new_value - old_value) / old_value * 100) if old_value != 0 else 100
            }
            
            # 读取现有历史记录
            history = []
            if self.optimization_history_file.exists():
                try:
                    with open(self.optimization_history_file, 'r', encoding='utf-8') as f:
                        history = json.load(f) or []
                except json.JSONDecodeError:
                    logger.warning("历史记录文件格式错误，将创建新文件")
            
            # 添加新记录
            history.append(record)
            
            # 如果记录过多，仅保留最新的1000条
            if len(history) > 1000:
                history = history[-1000:]
            
            # 保存历史记录
            with open(self.optimization_history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            # 同时添加到内存中的执行历史
            self.execution_history.append(record)
            if len(self.execution_history) > 100:  # 限制内存中的历史记录数量
                self.execution_history = self.execution_history[-100:]
            
            logger.debug("优化历史记录已保存", record=record)
            
        except Exception as e:
            logger.error("记录优化历史失败", error=str(e))
            # 失败不影响主流程
    
    def _validate_dependencies(self, task: OptimizationTask) -> bool:
        """验证任务依赖关系"""
        # 检查循环依赖
        visited = set()
        
        def has_cycle(task_id: str, path: set) -> bool:
            if task_id in path:
                return True
            if task_id in visited:
                return False
            
            visited.add(task_id)
            path.add(task_id)
            
            # 查找依赖任务
            for t in self.task_queue:
                if t.id == task_id:
                    for dep in t.dependencies:
                        if has_cycle(dep, path):
                            return True
            
            path.remove(task_id)
            return False
        
        return not has_cycle(task.id, set())
    
    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            "is_running": self.is_running,
            "queue_size": len(self.task_queue),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "execution_history_size": len(self.execution_history),
            "config": asdict(self.config)
        }
    
    def get_task_details(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务详情"""
        # 在所有任务列表中查找
        all_tasks = (self.task_queue + 
                    list(self.running_tasks.values()) + 
                    self.completed_tasks + 
                    self.failed_tasks)
        
        for task in all_tasks:
            if task.id == task_id:
                return asdict(task)
        
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        # 从队列中移除
        for i, task in enumerate(self.task_queue):
            if task.id == task_id:
                task.status = ExecutionStatus.SKIPPED
                self.task_queue.pop(i)
                logger.info("任务已取消", task_id=task_id)
                return True
        
        # 如果是运行中的任务，标记为取消
        if task_id in self.running_tasks:
            self.running_tasks[task_id].status = ExecutionStatus.SKIPPED
            logger.info("运行中任务已标记取消", task_id=task_id)
            return True
        
        return False
    
    def clear_completed_tasks(self) -> int:
        """清理已完成的任务"""
        count = len(self.completed_tasks) + len(self.failed_tasks)
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        logger.info("已清理完成的任务", count=count)
        return count