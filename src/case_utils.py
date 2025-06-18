from typing import Dict, Any

from src.core.services.variable_service import VariableService
from src.utils import singleton
from utils.config import BaseInfo
from utils.logger import logger
from utils.yaml_handler import YamlHandler

yaml_handler = YamlHandler()
base_info = BaseInfo()


@singleton
class LoadData:
    def __init__(self):

        self.yaml = yaml_handler
        self.test_data_dir = base_info.test_dir
        self.test_env = base_info.env
        self.vars = self._load_vars()

    def _load_test_datas(self) -> Dict[str, Any]:
        """加载现有的YAML配置文件"""
        return self.yaml.merge_yaml_files(self.test_data_dir + "/data").get(
            "test_data", {}
        )

    def _load_elements(self) -> Dict[str, Any]:
        """加载现有的YAML配置文件"""
        return self.yaml.merge_yaml_files(self.test_data_dir + "/elements").get(
            "elements", {}
        )

    def _load_vars(self) -> Dict[str, Any]:
        return self._merge_vars(self.yaml.load_yaml_dir(self.test_data_dir + "/vars"))

    def _merge_vars(self, vars_datas) -> Dict[str, Any]:
        """合并vars数据到test_data"""
        result = {}
        for vars_data in vars_datas:
            if vars_data:
                for env in ["dev", "test", "stage", "prod"]:
                    if env in vars_data.keys():
                        if env == self.test_env:
                            vars_data.update(vars_data.pop(env))
                        else:
                            vars_data.pop(env)
            result.update(vars_data)
        return result

    def return_data(self):
        return {
            "elements": self._load_elements(),
            "test_datas": self._load_test_datas(),
        }

    def return_vars(self):
        return self.vars

    def return_modules(self):
        return self.yaml.merge_yaml_files(self.test_data_dir + "/modules")


load_data = LoadData()


@singleton
def run_test_data():
    test_data = load_data.return_data()
    set_global_variables()
    return test_data


def set_global_variables():
    logger.info("当前测试环境: " + base_info.env)
    variable_manager = VariableService()
    if variables := load_data.return_vars():
        for var_name, var_value in variables.items():
            variable_manager.set_variable(var_name, var_value, "temp")


def load_test_cases(file_path):
    test_cases = yaml_handler.load_yaml(file_path).get("test_cases", [])
    return test_cases


@singleton
def load_moules():
    return load_data.return_modules()
