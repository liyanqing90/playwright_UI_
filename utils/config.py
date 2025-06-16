# config.py
import os
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings

from src.utils import singleton
from utils.logger import logger
from utils.yaml_handler import YamlHandler


class Browser(str, Enum):
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class Environment(str, Enum):
    DEV = "dev"
    TEST = "test"
    STAGE = "stage"
    PROD = "prod"


class ProjectManager:
    """项目管理器，负责动态发现和管理项目配置"""
    
    def __init__(self, config_path: str = "config/env_config.yaml"):
        self.config_path = Path(config_path)
        self.yaml_handler = YamlHandler()
        self._projects_cache = None
    
    def get_available_projects(self) -> list[str]:
        """获取所有可用的项目列表"""
        if self._projects_cache is None:
            self._load_projects()
        return list(self._projects_cache.keys())
    
    def _load_projects(self) -> dict:
        """从配置文件加载项目信息"""
        try:
            config = self.yaml_handler.load_yaml(self.config_path)
            if not config or "projects" not in config:
                raise ValueError("Invalid configuration: missing 'projects' section")
            
            self._projects_cache = config["projects"]
            return self._projects_cache
        except Exception as e:
            logger.error(f"Failed to load projects config: {e}")
            raise
    
    def get_project_config(self, project_name: str) -> dict:
        """获取指定项目的配置"""
        if self._projects_cache is None:
            self._load_projects()
        
        if project_name not in self._projects_cache:
            raise ValueError(f"Project '{project_name}' not found. Available projects: {self.get_available_projects()}")
        
        return self._projects_cache[project_name]
    
    def validate_project_config(self, project_name: str) -> bool:
        """验证项目配置的完整性"""
        try:
            config = self.get_project_config(project_name)
            
            # 检查必需的配置项
            required_fields = ["test_dir", "environments"]
            for field in required_fields:
                if field not in config:
                    logger.error(f"Project '{project_name}' missing required field: {field}")
                    return False
            
            # 检查环境配置
            environments = config["environments"]
            if not isinstance(environments, dict) or not environments:
                logger.error(f"Project '{project_name}' has invalid environments configuration")
                return False
            
            # 检查测试目录是否存在
            test_dir = Path(config["test_dir"])
            if not test_dir.exists():
                logger.warning(f"Test directory '{test_dir}' does not exist for project '{project_name}'")
            
            return True
        except Exception as e:
            logger.error(f"Error validating project config: {e}")
            return False


@singleton
class Config(BaseSettings):
    marker: Optional[str] = None
    keyword: Optional[str] = None
    headed: bool = True  # 将默认值改为 True
    browser: Browser = Browser.CHROMIUM
    env: Environment = Environment.PROD
    project: str = "demo"  # 改为字符串，支持动态项目
    base_url: str = ""
    test_dir: str = ""
    browser_config: Optional[dict] = None
    test_file: str = ""

    class Config:
        case_sensitive = False
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, 'project_manager', ProjectManager())
        self._update_config_based_on_env_and_project()
        self.validate_config()

    def validate_config(self):
        """验证配置是否有效"""
        # 转换项目名为小写
        if isinstance(self.project, str):
            self.project = self.project.lower()
        
        # 验证项目是否存在
        available_projects = self.project_manager.get_available_projects()
        if self.project not in available_projects:
            raise ValueError(
                f"Invalid project: {self.project}. Available projects: {', '.join(available_projects)}"
            )
        
        # 验证项目配置完整性
        if not self.project_manager.validate_project_config(self.project):
            raise ValueError(f"Invalid configuration for project: {self.project}")

    def _update_config_based_on_env_and_project(self):
        """根据环境和项目更新配置"""
        try:
            env_config = YamlHandler().load_yaml(Path("config/env_config.yaml"))
            if not env_config or not isinstance(env_config, dict):
                raise ValueError("Invalid YAML configuration")

            projects = env_config.get("projects", {})
            if not projects or not isinstance(projects, dict):
                raise ValueError("Missing or invalid projects configuration")

            # 使用项目管理器获取项目配置
            project_config = self.project_manager.get_project_config(self.project)
            
            # 获取环境URL
            environments = project_config.get("environments", {})
            self.base_url = environments.get(self.env.value)
            if not self.base_url:
                raise ValueError(
                    f"Environment {self.env.value} not found for project {self.project}"
                )

            # 设置测试数据目录
            self.test_dir = project_config.get("test_dir")
            self.browser_config = project_config.get(
                "browser_config", {"viewport": {"width": 1920, "height": 1080}}
            )

            # 设置环境变量
            os.environ["BASE_URL"] = self.base_url
            os.environ["TEST_DIR"] = str(self.test_dir)
            # os.environ['BROWSER_CONFIG'] = str(browser_config)

        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            raise ValueError(f"Configuration error: {str(e)}")

    def configure_environment(self):
        """配置运行环境"""
        os.environ["PWHEADED"] = "1" if self.headed else "0"
        os.environ["BROWSER"] = self.browser.value
        os.environ["TEST_ENV"] = self.env.value
        os.environ["TEST_PROJECT"] = self.project


class BaseInfo:
    def __init__(self):
        self.test_dir = os.environ.get("TEST_DIR", "test_data")
        self.base_dir = Path.cwd()
        self.env = os.environ.get("TEST_ENV", "test")
        self.project = os.environ.get("TEST_PROJECT", "demo")
