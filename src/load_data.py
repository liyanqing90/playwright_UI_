from typing import Dict, Any, List

from utils.excel_handler import ExcelHandler, ExcelTestCase
from utils.yaml_handler import YamlHandler


def _convert_to_cases(excel_cases: List[ExcelTestCase]):
    """转换为cases.yaml格式"""
    cases = []
    for case in excel_cases:
        # 使用Excel中的用例名称，去除空格并转换为小写作为测试用例ID
        case_name = f"test_{case.title.strip().lower().replace(' ', '_')}"

        case_info = {
            'name': case_name,
            'fixtures': []# 使用处理后的用例名称
        }

        # 添加其他必要的case级别信息
        if hasattr(case, 'skip') and case.skip:
            case_info['skip'] = "功能开发中"

        cases.append(case_info)
    return cases


def _convert_step(step: Dict[str, str]) -> Dict[str, Any]:
    """转换单个步骤"""
    converted = {
        'action': step['action'].lower()
    }

    # 添加选择器（如果有）
    if step['selector']:
        converted['selector'] = step['selector']

    # 添加值（如果有）
    if step['value']:
        converted['value'] = step['value']

    # 处理断言类型的步骤
    if converted['action'] == 'assertion':
        converted['type'] = 'text'

    return converted


def _convert_to_test_data(excel_cases: List[ExcelTestCase]):
    """转换为index.yaml格式"""
    test_data = {}
    for case in excel_cases:
        # 保持与cases中相同的命名方式
        case_name = f"test_{case.title.strip().lower().replace(' ', '_')}"

        case_data = {
            'description': case.title,
            'steps': []
        }

        # 转换步骤
        for step in case.steps:
            converted_step = _convert_step(step)
            if converted_step:
                case_data['steps'].append(converted_step)

        # 使用处理后的case name作为键
        test_data[case_name] = case_data

    return test_data


class DataConverter:
    def __init__(self, dir):
        self.test_data_dir = dir

        self.excel_handler = ExcelHandler(self.test_data_dir)
        self.yaml_data = self._load_yaml_data()

    def _load_yaml_data(self) -> Dict[str, Any]:
        self.yaml = YamlHandler()

        """加载现有的YAML配置文件"""
        return {
            'test_cases': self.yaml.load_yaml_dir(self.test_data_dir + '/cases')['test_cases'],
            'test_data': self._replace_steps(self.yaml.load_yaml_dir(self.test_data_dir + '/data')['test_data']),
            'elements': self.yaml.load_yaml_dir(self.test_data_dir + '/elements')['elements']
        }

    def _replace_steps(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        steps_dict = self.yaml.load_yaml_dir(self.test_data_dir + '/steps').get('steps')
        if steps_dict and test_data:
            # 遍历所有用例
            for case_name, case_data in test_data.items():
                for i, action in enumerate(case_data['steps']):
                    if "step_ref" in action.keys():
                        if step_value := steps_dict.get(action.get("step_ref")):
                            # 如果 step_value 是列表（多个步骤），替换当前步骤位置
                            if isinstance(step_value, list):
                                case_data['steps'][i:i + 1] = step_value  # 替换步骤
                            else:
                                action.update(step_value)  # 如果是字典，直接更新
                            del action["step_ref"]  # 删除原来的 "step" 键

                test_data[case_name] = case_data
        return test_data

    def convert_excel_data(self) -> Dict[str, Any]:
        """转换Excel数据为项目格式"""
        excel_cases = self.excel_handler.read_test_cases()

        converted_data = {
            'test_cases': _convert_to_cases(excel_cases),
            'test_data': _convert_to_test_data(excel_cases),
            'elements': self._convert_to_elements()
        }

        # 合并Excel数据和现有YAML数据
        merged_data = self._merge_data(converted_data)
        return merged_data

    def _convert_to_elements(self):
        """转换为elements.yaml格式"""
        return self.excel_handler.element_repository

    def _merge_data(self, excel_data) -> Dict[str, Any]:
        """合并Excel数据和YAML数据"""
        merged = {
            'test_cases': self._merge_cases(
                self.yaml_data.get('test_cases', []),
                excel_data.get('test_cases', {})
            ),
            'test_data': self._merge_test_data(
                self.yaml_data.get('test_data', {}),
                excel_data.get('test_data', {})
            ),
            'elements': self._merge_elements(
                self.yaml_data.get('elements', {}),
                excel_data.get('elements', {})
            )
        }
        return merged

    @staticmethod
    def _merge_cases(yaml_cases: List, excel_cases: List):
        """合并测试用例定义"""
        # 使用字典去重，Excel数据优先
        case_dict = {case['name']: case for case in yaml_cases}
        case_dict.update({case['name']: case for case in excel_cases})
        return list(case_dict.values())

    @staticmethod
    def _merge_test_data(yaml_data: Dict, excel_data: Dict):
        """合并测试数据"""
        # Excel数据优先
        merged = yaml_data.copy()
        merged.update(excel_data)
        return merged

    @staticmethod
    def _merge_elements(yaml_elements: Dict, excel_elements: Dict):
        """合并元素定位信息"""
        # Excel数据优先
        merged = yaml_elements.copy()
        merged.update(excel_elements)
        return merged
