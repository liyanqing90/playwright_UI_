# config.py
import os
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings

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


class Project(str, Enum):
    AHOH = "ahoh"
    OTHER_PROJECT = "other_project"


class Config(BaseSettings):
    marker: Optional[str] = None
    keyword: Optional[str] = None
    headed: bool = False
    browser: Browser = Browser.CHROMIUM
    env: Environment = Environment.PROD
    project: Project = Project.AHOH
    base_url: str = ""
    test_data_dir: str = ""

    class Config:
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._update_config_based_on_env_and_project()

    def _update_config_based_on_env_and_project(self):
        """根据环境和项目更新配置"""
        env_config = YamlHandler.load_yaml('config/env_config.yaml').get('projects')
        self.base_url = env_config.get(self.project).get(self.env)
        self.test_data_dir = Path.cwd() / env_config.get(self.project).get('test_data_dir')
        if self.env == Environment.DEV:
            self.base_url = "https://dev.example.com"
        elif self.env == Environment.TEST:
            self.base_url = "https://test.example.com"
        elif self.env == Environment.STAGE:
            self.base_url = "https://stage.example.com"
        elif self.env == Environment.PROD:
            self.base_url = "https://prod.example.com"

        if self.project == Project.AHOH:
            self.test_data_dir = "test_data/"

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
