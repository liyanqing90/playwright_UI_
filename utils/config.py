# config.py
import os
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings

from utils.yaml_handler import YamlHandler
from utils.logger import logger


class Browser(str, Enum):
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class Environment(str, Enum):
    DEV = "dev"
    TEST = "test"
    STAGE = "stage"
    PROD = "prod"


class Project(str, Enum):
    DEMO = "demo"
    HoloLive = "holo_live"
    OTHER_PROJECT = "other_project"


class Config(BaseSettings):
    marker: Optional[str] = None
    keyword: Optional[str] = None
    headed: bool = False
    browser: Browser = Browser.CHROMIUM
    env: Environment = Environment.PROD
    project: Project = Project.DEMO
    base_url: str = ""
    test_data_dir: str = ""
    class Config:
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._update_config_based_on_env_and_project()

    def _update_config_based_on_env_and_project(self):
        """根据环境和项目更新配置"""
        try:
            env_config = YamlHandler.load_yaml('config/env_config.yaml')
            print("*******")
            print(env_config)
            print(self.project)
            print(self.env)
            if not env_config or not isinstance(env_config, dict):
                raise ValueError("Invalid YAML configuration")
            
            projects = env_config.get('projects')
            if not projects or not isinstance(projects, dict):
                raise ValueError("Missing or invalid projects configuration")
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            env_config = {'projects': {}}
        project_config = env_config.get(self.project.value)
        if not project_config:
            raise ValueError(f"Project {self.project.value} not found in config")
            
        self.base_url = project_config['environments'].get(self.env.value)
        if not self.base_url:
            raise ValueError(f"Environment {self.env.value} not found for project {self.project.value}")
            
        self.test_data_dir = Path.cwd() / project_config.get('test_data_dir', 'test_data')
        if self.project == Project.DEMO:
            self.test_data_dir = "test_data/demo"

        elif self.project == Project.HoloLive:
            self.test_data_dir = "test_data/hololive"

        elif self.project == Project.OTHER_PROJECT:
            self.test_data_dir = "test_data/other_project"
        os.environ['BASE_URL'] = self.base_url
        os.environ['TEST_DATA_DIR'] = self.test_data_dir

    def configure_environment(self):
        """配置运行环境"""
        os.environ['PWHEADED'] = '1' if self.headed else '0'
        os.environ['BROWSER'] = self.browser.value
        os.environ['TEST_ENV'] = self.env.value
        os.environ['TEST_PROJECT'] = self.project.value
        
        # 打印环境变量配置
        print("配置的环境变量：")
        print(f"PWHEADED: {os.environ.get('PWHEADED')}")
        print(f"BROWSER: {os.environ.get('BROWSER')}")
        print(f"TEST_ENV: {os.environ.get('TEST_ENV')}")
        print(f"TEST_PROJECT: {os.environ.get('TEST_PROJECT')}")
        print(f"BASE_URL: {os.environ.get('BASE_URL')}")
        print(f"TEST_DATA_DIR: {os.environ.get('TEST_DATA_DIR')}")
