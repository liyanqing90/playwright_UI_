"""
断言管理器 - 统一处理断言并提供统计功能
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import allure
from pytest_check import check

from utils.logger import logger


@dataclass
class AssertionResult:
    """单个断言结果"""

    timestamp: datetime
    test_case: str
    step_description: str
    assertion_type: str  # 'soft' 或 'hard'
    passed: bool
    expected: Any
    actual: Any
    error_message: str = ""
    screenshot_path: str = ""


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

    统一处理所有断言，提供统计和报告功能
    """

    def __init__(self):
        self.stats = AssertionStats()
        self.current_test_case = ""

    def set_current_test_case(self, test_case_name: str):
        """设置当前测试用例名称"""
        self.current_test_case = test_case_name

    def record_assertion(
        self,
        assertion_type: str,
        condition: bool,
        message: str,
        expected: Any = None,
        actual: Any = None,
        step_description: str = "",
        screenshot: Optional[bytes] = None,
    ) -> bool:
        """记录断言结果

        Args:
            assertion_type: 断言类型 (软断言或硬断言)
            condition: 断言条件是否为真
            message: 断言消息
            expected: 期望值
            actual: 实际值
            step_description: 步骤描述
            screenshot: 截图数据

        Returns:
            bool: 断言是否成功

        Raises:
            AssertionError: 硬断言模式下如果断言失败则抛出异常
        """
        # 断言前处理
        # 这里可以添加事件通知等逻辑处理

        # 更新断言统计
        self.stats.total_assertions += 1

        # 如果实际值为空
        if actual is None or actual == "断言失败":
            actual = "未获取到实际值"

        # 生成一个唯一的截图文件名
        screenshot_path = ""
        if screenshot:
            timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S%f")
            screenshot_filename = f"screenshot_{timestamp_str}.png"
            screenshot_dir = os.path.join("reports", "screenshots")

            # 确保目录存在
            os.makedirs(screenshot_dir, exist_ok=True)

            # 生成完整路径
            screenshot_path = os.path.join(screenshot_dir, screenshot_filename)

            # 保存截图
            with open(screenshot_path, "wb") as f:
                f.write(screenshot)

            # 添加到Allure报告
            try:
                allure.attach(
                    screenshot,
                    name=f"断言截图_{step_description}",
                    attachment_type=allure.attachment_type.PNG,
                )
            except Exception as e:
                logger.warning(f"添加截图到Allure报告失败: {e}")

        # 保存断言结果
        result = AssertionResult(
            assertion_type=assertion_type,
            passed=condition,
            expected=expected,
            actual=actual,
            step_description=step_description,
            timestamp=datetime.now(),
            test_case=self.current_test_case or "",
            error_message=message if not condition else "",
            screenshot_path=screenshot_path,
        )

        self.stats.assertion_results.append(result)

        # 断言成功
        if condition:
            self.stats.passed_assertions += 1
            logger.debug(f"{assertion_type}断言通过: {step_description}")
            return True

        # 断言失败
        # 注意：failed_assertions是一个属性，不能直接修改
        # 在下面根据类型选择性地递增相关的计数器

        # 构造包含实际值的错误消息
        detailed_message = message
        # 根据断言类型记录和处理
        logger.error(message)

        if assertion_type.lower() == "soft":
            self.stats.failed_soft_assertions += 1
            check.fail(detailed_message)
        else:  # hard assertion
            self.stats.failed_hard_assertions += 1
            logger.error(f"硬断言失败: {detailed_message}")
            raise AssertionError(detailed_message)

        return False

    def get_stats(self) -> AssertionStats:
        """获取断言统计信息"""
        return self.stats

    def get_failed_assertions(
        self, assertion_type: str = None
    ) -> List[AssertionResult]:
        """
        获取失败的断言列表

        Args:
            assertion_type: 断言类型过滤 ('hard', 'soft', None表示全部)

        Returns:
            失败断言列表
        """
        failed_assertions = [r for r in self.stats.assertion_results if not r.passed]

        if assertion_type:
            failed_assertions = [
                r for r in failed_assertions if r.assertion_type == assertion_type
            ]

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
                "success_rate": round(self.stats.success_rate, 2),
            },
            "failed_assertions": [
                {
                    "timestamp": result.timestamp.isoformat(),
                    "test_case": result.test_case,
                    "step_description": result.step_description,
                    "assertion_type": result.assertion_type,
                    "expected": str(result.expected),
                    "actual": str(result.actual),
                    "error_message": result.error_message,
                }
                for result in self.get_failed_assertions()
            ],
        }

    def save_report(self, file_path: str = "reports/assertion_report.json"):
        """保存断言报告到文件"""
        report = self.generate_report()

        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    def reset_stats(self):
        """重置统计信息"""
        self.stats = AssertionStats()
        logger.debug("断言统计信息已重置")


# 全局断言管理器实例
assertion_manager = AssertionManager()
