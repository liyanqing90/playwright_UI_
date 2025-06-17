"""服务模块

提供各种功能服务的接口定义和实现。"""

from .assertion_service import AssertionService, AssertionOperations
from .base_service import BaseService
from .element_service import ElementService, ElementOperations
from .navigation_service import NavigationService, NavigationOperations
from .variable_service import VariableService, VariableOperations
from .wait_service import WaitService, WaitOperations

__all__ = [
    "BaseService",
    "ElementService",
    "ElementOperations",
    "NavigationService",
    "NavigationOperations",
    "WaitService",
    "WaitOperations",
    "AssertionService",
    "AssertionOperations",
    "VariableService",
    "VariableOperations",
]
