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
            "test_data": self._replace_steps(
                self.yaml.load_yaml_dir(self.test_data_dir + "/data")["test_data"]
            ),
            "elements": self.yaml.load_yaml_dir(self.test_data_dir + "/elements")[
                "elements"
            ],
        }

    def _replace_steps(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        steps_dict = self.yaml.load_yaml_dir(self.test_data_dir + "/steps").get("steps")
        if steps_dict and test_data:
            # 遍历所有用例
            for case_name, case_data in test_data.items():
                for i, action in enumerate(case_data["steps"]):
                    if "step_ref" in action.keys():
                        if step_value := steps_dict.get(action.get("step_ref")):
                            # 如果 step_value 是列表（多个步骤），替换当前步骤位置
                            if isinstance(step_value, list):
                                case_data["steps"][i : i + 1] = step_value  # 替换步骤
                            else:
                                action.update(step_value)  # 如果是字典，直接更新
                            del action["step_ref"]  # 删除原来的 "step" 键

                test_data[case_name] = case_data
        return test_data

    def return_data(self):
        return self.yaml_data
