"""分层架构与插件系统职责划分重构计划实施

根据优化计划，明确核心服务和插件系统的职责边界，
消除重复功能，统一接口设计。
"""

from enum import Enum
from typing import Dict, List, Any

from utils.logger import logger


class ComponentType(Enum):
    """组件类型"""
    CORE_SERVICE = "core_service"  # 核心服务
    PLUGIN = "plugin"  # 插件
    SHARED_INTERFACE = "shared_interface"  # 共享接口
    DEPRECATED = "deprecated"  # 待废弃

class RefactorAction(Enum):
    """重构动作"""
    KEEP_IN_CORE = "keep_in_core"  # 保留在核心
    MOVE_TO_PLUGIN = "move_to_plugin"  # 移动到插件
    MOVE_TO_CORE = "move_to_core"  # 移动到核心
    REMOVE_DUPLICATE = "remove_duplicate"  # 移除重复
    CREATE_INTERFACE = "create_interface"  # 创建接口
    DEPRECATE = "deprecate"  # 废弃

class ResponsibilityMatrix:
    """职责划分矩阵
    
    定义每个功能模块应该属于核心服务还是插件系统。
    """
    
    # 核心服务职责：基础、稳定、高频、必需的功能
    CORE_RESPONSIBILITIES = {
        # 测试执行引擎
        'test_execution': {
            'component_type': ComponentType.CORE_SERVICE,
            'reason': '框架核心功能，必需且稳定',
            'location': 'src/automation/test_runner.py'
        },
        
        # 基础元素操作
        'element_operations': {
            'component_type': ComponentType.CORE_SERVICE,
            'reason': '基础UI操作，高频使用',
            'location': 'src/core/services/element_service.py',
            'functions': ['click', 'fill', 'hover', 'get_text', 'is_visible']
        },
        
        # 基础导航功能
        'navigation': {
            'component_type': ComponentType.CORE_SERVICE,
            'reason': '基础导航功能，框架必需',
            'location': 'src/core/services/navigation_service.py',
            'functions': ['navigate', 'go_back', 'go_forward', 'refresh']
        },
        
        # 基础等待策略
        'wait_operations': {
            'component_type': ComponentType.CORE_SERVICE,
            'reason': '基础等待功能，稳定且必需',
            'location': 'src/core/services/wait_service.py',
            'functions': ['wait_for_element', 'wait_for_timeout', 'wait_for_condition']
        },
        
        # 基础断言功能
        'basic_assertions': {
            'component_type': ComponentType.CORE_SERVICE,
            'reason': '基础断言功能，测试框架必需',
            'location': 'src/core/services/assertion_service.py',
            'functions': ['assert_visible', 'assert_text_equals', 'assert_url_contains']
        },
        
        # 变量管理
        'variable_management': {
            'component_type': ComponentType.CORE_SERVICE,
            'reason': '基础变量功能，框架基础设施',
            'location': 'src/core/services/variable_service.py'
        },
        
        # 配置管理核心
        'config_management': {
            'component_type': ComponentType.CORE_SERVICE,
            'reason': '框架配置基础设施',
            'location': 'src/core/config.py'
        },
        
        # 依赖注入容器
        'dependency_injection': {
            'component_type': ComponentType.CORE_SERVICE,
            'reason': '框架基础设施',
            'location': 'src/core/container.py'
        },
        
        # 事件总线
        'event_bus': {
            'component_type': ComponentType.CORE_SERVICE,
            'reason': '框架通信基础设施',
            'location': 'src/core/events.py'
        }
    }
    
    # 插件系统职责：可选、扩展、特定场景的功能
    PLUGIN_RESPONSIBILITIES = {
        # 高级断言功能
        'advanced_assertions': {
            'component_type': ComponentType.PLUGIN,
            'reason': '扩展功能，可选使用',
            'location': 'plugins/assertion_commands/',
            'functions': ['soft_assertions', 'batch_assertions', 'retry_assertions', 'json_schema_assertions']
        },
        
        # 性能监控
        'performance_monitoring': {
            'component_type': ComponentType.PLUGIN,
            'reason': '可选功能，特定场景使用',
            'location': 'plugins/performance_management/'
        },
        
        # 网络操作
        'network_operations': {
            'component_type': ComponentType.PLUGIN,
            'reason': '特定场景功能，非必需',
            'location': 'plugins/network_operations/'
        },
        
        # 文件操作
        'file_operations': {
            'component_type': ComponentType.PLUGIN,
            'reason': '特定场景功能，非核心',
            'location': 'plugins/file_operations/'
        },
        
        # 数据生成
        'data_generation': {
            'component_type': ComponentType.PLUGIN,
            'reason': '扩展功能，项目特定',
            'location': 'plugins/data_generator/'
        },
        
        # 通知服务
        'notification_service': {
            'component_type': ComponentType.PLUGIN,
            'reason': '可选功能，非核心',
            'location': 'plugins/notification/'
        },
        
        # 报告处理
        'report_processing': {
            'component_type': ComponentType.PLUGIN,
            'reason': '扩展功能，可定制',
            'location': 'plugins/report_generator/'
        },
        
        # 存储操作
        'storage_operations': {
            'component_type': ComponentType.PLUGIN,
            'reason': '特定场景功能',
            'location': 'plugins/storage/'
        }
    }
    
    # 重复功能识别
    DUPLICATE_FUNCTIONS = {
        'assertion_functions': {
            'core_location': 'src/core/services/assertion_service.py',
            'plugin_location': 'plugins/assertion_commands/plugin.py',
            'duplicated_functions': [
                'assert_text_equals',
                'assert_element_visible',
                'assert_url_contains'
            ],
            'action': RefactorAction.REMOVE_DUPLICATE,
            'strategy': '保留核心基础断言，插件提供高级断言功能'
        },
        
        'performance_monitoring': {
            'core_location': 'src/core/services/base_service.py',
            'plugin_location': 'plugins/performance_management/',
            'duplicated_functions': ['_record_operation'],
            'action': RefactorAction.REMOVE_DUPLICATE,
            'strategy': '核心提供基础性能记录接口，插件提供详细分析'
        }
    }

class RefactorPlan:
    """重构计划执行器"""
    
    def __init__(self):
        self.matrix = ResponsibilityMatrix()
        self.refactor_steps = []
    
    def generate_refactor_plan(self) -> List[Dict[str, Any]]:
        """生成重构计划
        
        Returns:
            List[Dict[str, Any]]: 重构步骤列表
        """
        plan = []
        
        # 第一阶段：确定核心功能边界
        plan.extend(self._phase1_define_boundaries())
        
        # 第二阶段：消除重复功能
        plan.extend(self._phase2_eliminate_duplicates())
        
        # 第三阶段：统一接口设计
        plan.extend(self._phase3_unify_interfaces())
        
        # 第四阶段：测试和验证
        plan.extend(self._phase4_testing_validation())
        
        return plan
    
    def _phase1_define_boundaries(self) -> List[Dict[str, Any]]:
        """第一阶段：确定核心功能边界"""
        steps = []
        
        # 核心服务边界确认
        steps.append({
            'phase': 1,
            'step': 'core_boundary_definition',
            'description': '确认核心服务边界，保留基础、稳定、高频功能',
            'actions': [
                '审查现有核心服务实现',
                '确认ElementService、NavigationService、WaitService、AssertionService为核心',
                '移除核心服务中的非必需功能'
            ],
            'estimated_time': '1周'
        })
        
        # 插件边界确认
        steps.append({
            'phase': 1,
            'step': 'plugin_boundary_definition',
            'description': '确认插件系统边界，包含可选、扩展、特定场景功能',
            'actions': [
                '审查现有插件实现',
                '确认高级断言、性能监控、网络操作等为插件',
                '标准化插件接口'
            ],
            'estimated_time': '1周'
        })
        
        return steps
    
    def _phase2_eliminate_duplicates(self) -> List[Dict[str, Any]]:
        """第二阶段：消除重复功能"""
        steps = []
        
        # 断言功能重构
        steps.append({
            'phase': 2,
            'step': 'assertion_refactor',
            'description': '重构断言功能，消除核心服务和插件间的重复',
            'actions': [
                '保留核心AssertionService的基础断言功能',
                '移除插件中与核心重复的基础断言',
                '插件专注于高级断言功能（软断言、批量断言、重试断言等）',
                '建立清晰的断言功能分层'
            ],
            'files_affected': [
                'src/core/services/assertion_service.py',
                'plugins/assertion_commands/plugin.py'
            ],
            'estimated_time': '1周'
        })
        
        # 性能监控重构
        steps.append({
            'phase': 2,
            'step': 'performance_refactor',
            'description': '重构性能监控功能，明确核心和插件职责',
            'actions': [
                '核心服务提供基础性能记录接口',
                '插件提供详细的性能分析和管理功能',
                '统一性能数据格式和接口'
            ],
            'files_affected': [
                'src/core/services/base_service.py',
                'plugins/performance_management/'
            ],
            'estimated_time': '1周'
        })
        
        return steps
    
    def _phase3_unify_interfaces(self) -> List[Dict[str, Any]]:
        """第三阶段：统一接口设计"""
        steps = []
        
        # 服务接口标准化
        steps.append({
            'phase': 3,
            'step': 'service_interface_standardization',
            'description': '标准化服务接口，实现ServiceInterface',
            'actions': [
                '所有核心服务实现ServiceInterface',
                '支持配置驱动的服务管理',
                '实现服务生命周期管理',
                '优化依赖注入机制'
            ],
            'files_affected': [
                'src/core/interfaces/service_interface.py',
                'src/core/services/*.py',
                'src/core/container.py'
            ],
            'estimated_time': '1周'
        })
        
        # 插件接口标准化
        steps.append({
            'phase': 3,
            'step': 'plugin_interface_standardization',
            'description': '标准化插件接口，实现PluginInterface',
            'actions': [
                '所有插件实现PluginInterface',
                '统一插件元数据格式',
                '标准化插件生命周期管理',
                '优化插件加载机制'
            ],
            'files_affected': [
                'src/core/interfaces/plugin_interface.py',
                'plugins/*/plugin.py',
                'src/core/plugin_manager.py'
            ],
            'estimated_time': '1周'
        })
        
        return steps
    
    def _phase4_testing_validation(self) -> List[Dict[str, Any]]:
        """第四阶段：测试和验证"""
        steps = []
        
        steps.append({
            'phase': 4,
            'step': 'comprehensive_testing',
            'description': '全面测试重构后的系统',
            'actions': [
                '单元测试：测试所有核心服务',
                '集成测试：测试服务间协作',
                '插件测试：测试插件加载和功能',
                '性能测试：验证重构后的性能',
                '兼容性测试：确保向后兼容'
            ],
            'estimated_time': '1周'
        })
        
        return steps
    
    def print_refactor_plan(self):
        """打印重构计划"""
        plan = self.generate_refactor_plan()
        
        logger.info("=== 分层架构与插件系统职责划分重构计划 ===")
        logger.info(f"总计划步骤数: {len(plan)}")
        logger.info(f"预计总时间: 5周")
        logger.info("")
        
        for step in plan:
            logger.info(f"阶段 {step['phase']}: {step['step']}")
            logger.info(f"描述: {step['description']}")
            logger.info(f"预计时间: {step['estimated_time']}")
            
            if 'actions' in step:
                logger.info("行动项:")
                for action in step['actions']:
                    logger.info(f"  - {action}")
            
            if 'files_affected' in step:
                logger.info("影响文件:")
                for file in step['files_affected']:
                    logger.info(f"  - {file}")
            
            logger.info("")

if __name__ == "__main__":
    refactor_plan = RefactorPlan()
    refactor_plan.print_refactor_plan()