
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
            'name': case_name,  # 使用处理后的用例名称
        }

        # 添加其他必要的case级别信息
        if hasattr(case, 'skip') and case.skip:
            case_info['skip'] = "功能开发中"

        cases.append(case_info)
    return cases

def _convert_to_test_data(excel_cases: List[ExcelTestCase]):
    """转换为index.yaml格式"""
    test_data = {}
    for case in excel_cases:
        # 保持与cases中相同的命名方式
        case_name = f"test_{case.title.strip().lower().replace(' ', '_')}"

        case_data = {
            'description': case.title,
            'steps': case.steps
        }

        # 使用处理后的case name作为键
        test_data[case_name] = case_data

    return test_data


class DataConverter:
    def __init__(self, dir):
        self.test_data_dir = dir

        self.excel_handler = ExcelHandler(self.test_data_dir)



    def convert_excel_data(self) -> Dict[str, Any]:
        """转换Excel数据为项目格式"""
        excel_cases = self.excel_handler.read_test_cases()

        converted_data = {
            'test_cases': _convert_to_cases(excel_cases),
            'test_data': _convert_to_test_data(excel_cases),
            'elements': self._convert_to_elements()
        }
        return converted_data


    def _convert_to_elements(self):
        """转换为elements.yaml格式"""
        return self.excel_handler.element_repository



data_merger = DataConverter("./files/excel")
data = data_merger.convert_excel_data()
test_cases = data['test_cases']
test_data = data['test_data']
elements = data['elements']

output_directory = './files/output'  # 指定输出目录

yaml = YamlHandler()

for key, value in data.items():
    print(key)
    yaml.save_to_yaml({key: value}, output_directory, key)