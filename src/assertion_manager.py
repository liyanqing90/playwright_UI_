"""
断言管理器 - 统一处理软硬断言并提供统计功能
"""

from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path

from utils.logger import logger
from pytest_check import check


@dataclass
class AssertionResult:
    """单个断言结果"""
    timestamp: datetime
    test_case: str
    step_description: str
    assertion_type: str  # 'hard' or 'soft'
    passed: bool
    expected: Any
    actual: Any
    error_message: str = ""


@dataclass
class AssertionStats:
    """断言统计信息"""
    total_assertions: int = 0
    passed_assertions: int = 0
    failed_soft_assertions: int = 0
    failed_hard_assertions: int = 0
    assertion_results: List[AssertionResult] = field(default_factory=list)
    
    @property
    def failed_assertions(self) -> int:
        """总失败断言数"""
        return self.failed_soft_assertions + self.failed_hard_assertions
    
    @property
    def success_rate(self) -> float:
        """断言成功率"""
        if self.total_assertions == 0:
            return 0.0
        return (self.passed_assertions / self.total_assertions) * 100


class AssertionManager:
    """
    断言管理器
    
    统一处理软硬断言，保持原有行为：
    - 硬断言失败时立即终止测试
    - 软断言失败时记录错误但继续执行
    
    同时提供断言统计和报告功能
    """
    
    def __init__(self):
        self.stats = AssertionStats()
        self.current_test_case = ""
        
    def set_current_test_case(self, test_case_name: str):
        """设置当前测试用例名称"""
        self.current_test_case = test_case_name
        
    def hard_assert(self, condition: bool, message: str, expected: Any = None, 
                   actual: Any = None, step_description: str = "") -> None:
        """
        硬断言：失败时立即终止测试执行
        
        Args:
            condition: 断言条件
            message: 错误消息
            expected: 期望值
            actual: 实际值
            step_description: 步骤描述
        """
        self.stats.total_assertions += 1
        
        result = AssertionResult(
            timestamp=datetime.now(),
            test_case=self.current_test_case,
            step_description=step_description,
            assertion_type='hard',
            passed=condition,
            expected=expected,
            actual=actual,
            error_message=message if not condition else ""
        )
        
        self.stats.assertion_results.append(result)
        
        if condition:
            self.stats.passed_assertions += 1
            logger.debug(f"硬断言通过: {step_description}")
        else:
            self.stats.failed_hard_assertions += 1
            logger.error(f"硬断言失败: {message}")
            
            # 创建硬断言异常并标记
            error = AssertionError(message)
            error._hard_assert = True
            error._expected = expected
            error._actual = actual
            raise error
            
    def soft_assert(self, condition: bool, message: str, expected: Any = None,
                   actual: Any = None, step_description: str = "") -> bool:
        """
        软断言：失败时记录错误但继续执行
        
        Args:
            condition: 断言条件
            message: 错误消息
            expected: 期望值
            actual: 实际值
            step_description: 步骤描述
            
        Returns:
            断言是否通过
        """
        self.stats.total_assertions += 1
        
        result = AssertionResult(
            timestamp=datetime.now(),
            test_case=self.current_test_case,
            step_description=step_description,
            assertion_type='soft',
            passed=condition,
            expected=expected,
            actual=actual,
            error_message=message if not condition else ""
        )
        
        self.stats.assertion_results.append(result)
        
        if condition:
            self.stats.passed_assertions += 1
            logger.debug(f"软断言通过: {step_description}")
        else:
            self.stats.failed_soft_assertions += 1
            logger.error(f"软断言失败: {message}")
            check.fail(message)
            
        return condition
        
    def get_stats(self) -> AssertionStats:
        """获取断言统计信息"""
        return self.stats
        
    def get_failed_assertions(self, assertion_type: str = None) -> List[AssertionResult]:
        """
        获取失败的断言列表
        
        Args:
            assertion_type: 断言类型过滤 ('hard', 'soft', None表示全部)
            
        Returns:
            失败断言列表
        """
        failed_assertions = [r for r in self.stats.assertion_results if not r.passed]
        
        if assertion_type:
            failed_assertions = [r for r in failed_assertions if r.assertion_type == assertion_type]
            
        return failed_assertions
        
    def generate_report(self) -> Dict[str, Any]:
        """生成断言报告"""
        return {
            "summary": {
                "total_assertions": self.stats.total_assertions,
                "passed_assertions": self.stats.passed_assertions,
                "failed_assertions": self.stats.failed_assertions,
                "failed_soft_assertions": self.stats.failed_soft_assertions,
                "failed_hard_assertions": self.stats.failed_hard_assertions,
                "success_rate": round(self.stats.success_rate, 2)
            },
            "failed_assertions": [
                {
                    "timestamp": result.timestamp.isoformat(),
                    "test_case": result.test_case,
                    "step_description": result.step_description,
                    "assertion_type": result.assertion_type,
                    "expected": str(result.expected),
                    "actual": str(result.actual),
                    "error_message": result.error_message
                }
                for result in self.get_failed_assertions()
            ]
        }
        
    def save_report(self, file_path: str = "reports/assertion_report.json"):
        """保存断言报告到文件"""
        report = self.generate_report()
        
        # 确保目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
    def reset_stats(self):
        """重置统计信息"""
        self.stats = AssertionStats()
        logger.debug("断言统计信息已重置")


# 全局断言管理器实例
assertion_manager = AssertionManager()
