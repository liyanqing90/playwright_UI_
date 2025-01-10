from typing import Dict, Any, List

import yaml

from utils.config import Config
from utils import logger
from utils.excel_handler import ExcelHandler, ExcelTestCase


def _convert_to_cases(excel_cases: List[ExcelTestCase]) -> Dict[str, List]:
    """转换为cases.yaml格式"""
    cases = []
    for case in excel_cases:
        # 使用Excel中的用例名称，去除空格并转换为小写作为测试用例ID
        case_name = f"test_{case.title.strip().lower().replace(' ', '_')}"

        case_info = {
            'name': case_name,  # 使用处理后的用例名称
            'description': case.title,
            'fixtures': []  # 默认fixture
        }

        # 添加其他必要的case级别信息
        if hasattr(case, 'skip') and case.skip:
            case_info['skip'] = "功能开发中"

        cases.append(case_info)

    return {'test_cases': cases}


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


def _convert_to_test_data(excel_cases: List[ExcelTestCase]) -> Dict[str, Dict]:
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

    return {'test_data': test_data}


class DataConverter:
    def __init__(self, config):
        self.test_data_dir = config.test_data_dir

        self.excel_handler = ExcelHandler(config.test_data_dir)
        self.yaml_data = self._load_yaml_data()

    def _load_yaml_data(self) -> Dict[str, Any]:
        """加载现有的YAML配置文件"""
        return {
            'cases': self._load_yaml_file(self.test_data_dir + '/cases/cases.yaml'),
            'test_data': self._load_yaml_file(self.test_data_dir + '/data/index.yaml'),
            'elements': self._load_yaml_file(self.test_data_dir + '/elements/elements.yaml')
        }

    @staticmethod
    def _load_yaml_file(file_path: str) -> Dict[str, Any]:
        """加载单个YAML文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载YAML文件失败 {file_path}: {str(e)}")
            return {}

    def convert_excel_data(self) -> Dict[str, Any]:
        """转换Excel数据为项目格式"""
        excel_cases = self.excel_handler.read_test_cases()

        converted_data = {
            'cases': _convert_to_cases(excel_cases),
            'test_data': _convert_to_test_data(excel_cases),
            'elements': self._convert_to_elements()
        }

        # 合并Excel数据和现有YAML数据
        merged_data = self._merge_data(converted_data)
        return merged_data

    def _convert_to_elements(self) -> Dict[str, Dict]:
        """转换为elements.yaml格式"""
        return {
            'elements': self.excel_handler.element_repository
        }

    def _merge_data(self, excel_data: Dict[str, Any]) -> Dict[str, Any]:
        """合并Excel数据和YAML数据"""
        merged = {
            'cases': self._merge_cases(
                self.yaml_data['cases'].get('test_cases', []),
                excel_data['cases']['test_cases']
            ),
            'test_data': self._merge_test_data(
                self.yaml_data['test_data'].get('test_data', {}),
                excel_data['test_data']['test_data']
            ),
            'elements': self._merge_elements(
                self.yaml_data['elements'].get('elements', {}),
                excel_data['elements']['elements']
            )
        }
        return merged

    @staticmethod
    def _merge_cases(yaml_cases: List, excel_cases: List) -> Dict[str, List]:
        """合并测试用例定义"""
        # 使用字典去重，Excel数据优先
        case_dict = {case['name']: case for case in yaml_cases}
        case_dict.update({case['name']: case for case in excel_cases})
        return {'test_cases': list(case_dict.values())}

    @staticmethod
    def _merge_test_data(yaml_data: Dict, excel_data: Dict) -> Dict[str, Dict]:
        """合并测试数据"""
        # Excel数据优先
        merged = yaml_data.copy()
        merged.update(excel_data)
        return {'test_data': merged}

    @staticmethod
    def _merge_elements(yaml_elements: Dict, excel_elements: Dict) -> Dict[str, Dict]:
        """合并元素定位信息"""
        # Excel数据优先
        merged = yaml_elements.copy()
        merged.update(excel_elements)
        return {'elements': merged}
