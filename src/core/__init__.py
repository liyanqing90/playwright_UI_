"""核心模块

提供基础页面类、服务容器和各种服务。
"""

from .base_page import BasePage
from .container import ServiceContainer
from .services.assertion_service import AssertionService
from .services.element_service import ElementService
from .services.navigation_service import NavigationService
from .services.variable_service import VariableService
from .services.wait_service import WaitService

__all__ = [
    'BasePage',
    'ServiceContainer',
    'ElementService',
    'NavigationService',
    'WaitService',
    'AssertionService',
    'VariableService',
]