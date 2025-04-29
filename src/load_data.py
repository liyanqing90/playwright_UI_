from typing import Dict, Any

from utils.yaml_handler import YamlHandler


class LoadData:
    def __init__(self, dir):
        self.test_data_dir = dir

        self.yaml_data = self._load_yaml_data()

    def _load_yaml_data(self) -> Dict[str, Any]:
        self.yaml = YamlHandler()

        """加载现有的YAML配置文件"""
        return {
            "test_cases": self.yaml.load_yaml_dir(self.test_data_dir + "/cases")[
                "test_cases"
            ],
            "test_data": self.yaml.load_yaml_dir(self.test_data_dir + "/data")[
                "test_data"
            ],
            "elements": self.yaml.load_yaml_dir(self.test_data_dir + "/elements")[
                "elements"
            ],
            "vars": self.yaml.load_yaml_dir(self.test_data_dir + "/vars"),
        }

    def return_data(self):
        return self.yaml_data
