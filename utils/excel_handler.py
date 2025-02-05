import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

from utils.logger import logger


class ExcelTestCase:
    # 定义列名常量
    COLUMN_CASE_ID = '用例ID'
    COLUMN_CASE_NAME = '用例名称'
    COLUMN_ACTION = '操作'
    COLUMN_ELEMENT = '元素'
    COLUMN_PRIORITY = '优先级'
    COLUMN_EXPECT = '预期结果'
    COLUMN_SKIP = '是否跳过'
    COLUMN_VALUE = '数据'

    def __init__(self, module: str, case_id: str, title: str, steps: List[Dict[str, Any]] = None,
                 priority: str = "P2", tags: List[str] = None):
        self.module = module
        self.case_id = case_id
        self.title = title
        self.steps = steps or []
        self.priority = priority
        self.tags = tags or []


def _is_sheet_skipped(df: pd.DataFrame) -> bool:
    """检查sheet是否被标记为跳过"""
    skip_value = df.get(ExcelTestCase.COLUMN_SKIP, '').iloc[0] if not df.empty else ''
    return str(skip_value).strip().lower() in ['是', 'y', 'yes', 'true', '1']


def _is_new_case(case_name: str) -> bool:
    """检查是否是新的测试用例"""
    return bool(case_name and not pd.isna(case_name) and case_name.lower() not in ['nan', 'none', 'null'])


def _is_case_skipped(row: pd.Series) -> bool:
    """检查用例是否被标记为跳过"""
    skip_value = row.get(ExcelTestCase.COLUMN_SKIP, '')
    return not pd.isna(skip_value) and str(skip_value).strip().lower() in ['是', 'y', 'yes', 'true', '1']


def _create_test_case(case: ExcelTestCase, steps: List[Dict[str, str]]) -> ExcelTestCase:
    """创建完整的测试用例"""
    case.steps = steps
    return case


def _get_existing_cases() -> List[ExcelTestCase]:
    """获取已存在的测试用例列表"""
    return []  # 可以根据需要实现用例计数逻辑


def convert_to_yaml_format(test_cases: List[ExcelTestCase]) -> Dict:
    """
    将测试用例转换为YAML格式
    Args:
        test_cases: 测试用例列表
    Returns:
        YAML格式的测试用例
    """
    yaml_cases = []
    for case in test_cases:
        yaml_case = {
            'name': f"{case.case_id}_{case.title}",
            'description': case.title,
            'allure': {
                'feature': case.module,
                'story': case.title,
                'severity': 'critical' if case.priority in ['P0', 'P1'] else 'normal'
            },
            'tags': case.tags + [case.priority],
            'steps': []
        }

        # 添加步骤
        for step in case.steps:
            yaml_step = {
                'name': step['name'] or case.title,  # 如果步骤名为空，使用用例标题
                'action': step['action'],
                'description': step['description']
            }

            # 只添加非空的参数
            if step['selector'].strip():
                yaml_step['selector'] = step['selector']
            if step['value'].strip():
                if step['action'].lower() in ['press_key', '按键']:
                    yaml_step['key'] = step['value']
                else:
                    yaml_step['value'] = step['value']

            yaml_case['steps'].append(yaml_step)

        yaml_cases.append(yaml_case)
        logger.debug(f"转换用例: {yaml_case['name']}")

    return {'test_cases': yaml_cases}


def _initialize_case(case_name: str, sheet: str, excel_path: str) -> ExcelTestCase:
    """初始化新的测试用例"""
    excel_name = os.path.splitext(os.path.basename(excel_path))[0]
    case_id = f"{excel_name}_{len(_get_existing_cases()) + 1:03d}"
    return ExcelTestCase(module=sheet, case_id=case_id, title=case_name)


def get_sheet_names(workbook) -> List[str]:
    """获取所有sheet名称（排除第一个sheet，因为它是元素对象库）"""
    return workbook.sheet_names[1:]


class ExcelHandler:
    def __init__(self, directory: str):
        self.directory = directory
        self.element_repository = {}

    def _load_element_repository(self, excel_path):
        """加载元素对象库（第一个sheet）"""
        try:
            df = pd.read_excel(excel_path, sheet_name=0)
            required_columns = ['控件名称', '定位方式', '值']

            if not all(col in df.columns for col in required_columns):
                logger.error(f"元素对象库格式不正确，缺少必要的列: {required_columns}")
                return

            for _, row in df.iterrows():
                name = str(row['控件名称']).strip()
                selector_type = str(row['定位方式']).strip()
                selector_value = str(row['值']).strip()

                if not name or not selector_value:
                    continue

                selector = f"{selector_type}={selector_value}" if selector_type and selector_type not in ['nan',
                                                                                                          'css selector'] else selector_value
                self.element_repository[name] = selector

        except Exception as e:
            logger.error(f"加载元素对象库失败: {str(e)}")

    def read_test_cases(self) -> List[ExcelTestCase]:
        """读取指定目录下的所有Excel文件中的测试用例"""
        excel_files = get_excel_files(self.directory)
        all_test_cases = []

        if not excel_files:
            logger.warning(f"指定目录 {self.directory} 下没有找到任何Excel文件")
            return []

        for excel_file in excel_files:
            try:
                self._load_element_repository(str(excel_file))
                test_cases = self._read_test_cases(str(excel_file))
                all_test_cases.extend(test_cases)
            except Exception as e:
                logger.error(f"处理Excel文件 {excel_file} 失败: {str(e)}")
                continue

        if not all_test_cases:
            raise ValueError("没有找到可执行的测试用例")
        return all_test_cases

    def _read_test_cases(self, excel_path: str, sheet_name: str = None) -> List[ExcelTestCase]:
        """读取Excel中的测试用例"""
        try:
            workbook = pd.ExcelFile(excel_path)
        except Exception as e:
            logger.error(f"加载Excel文件失败: {str(e)}")
            raise
        sheets = [sheet_name] if sheet_name else get_sheet_names(workbook)
        test_cases = []

        for sheet in sheets:
            try:
                df = pd.read_excel(excel_path, sheet_name=sheet)
                if _is_sheet_skipped(df):
                    continue

                current_case = None
                steps = []

                for _, row in df.iterrows():
                    if pd.isna(row).all():
                        continue

                    case_name = str(row.get(ExcelTestCase.COLUMN_CASE_NAME, '')).strip()
                    if _is_new_case(case_name):
                        if current_case and steps:
                            test_cases.append(_create_test_case(current_case, steps))
                            steps = []

                        if _is_case_skipped(row):
                            current_case = None
                            continue

                        current_case = _initialize_case(case_name, sheet, excel_path)

                    step = self._create_step(row, current_case)
                    if step:
                        steps.append(step)

                # 保存最后一个用例
                if current_case and steps:
                    test_cases.append(_create_test_case(current_case, steps))

            except Exception as e:
                logger.error(f"读取sheet {sheet} 失败: {str(e)}")
                continue

        if not test_cases:
            raise ValueError("没有找到可执行的测试用例")

        return test_cases

    def _create_step(self, row: pd.Series, current_case: ExcelTestCase) -> Optional[Dict[str, str]]:
        """创建测试步骤"""
        action_value = row.get(ExcelTestCase.COLUMN_ACTION, '')
        if pd.isna(action_value) or not str(action_value).strip() or not current_case:
            return None

        element_name = str(row.get(ExcelTestCase.COLUMN_ELEMENT, '')).strip()
        element_selector = self._resolve_element_selector(element_name)
        step_name = element_name if element_name and element_name.lower() != 'nan' else current_case.title

        step = {
            'name': step_name,
            'action': str(action_value).strip(),
            'selector': element_selector,
            'value': str(row.get(ExcelTestCase.COLUMN_VALUE, '')).strip(),
            'description': str(row.get(ExcelTestCase.COLUMN_EXPECT, '')).strip()
        }

        return {k: ('' if pd.isna(v) or str(v).lower() in ['nan', 'none', 'null'] else v) for k, v in step.items()}

    def _resolve_element_selector(self, element_name: str) -> str:
        """解析元素选择器"""
        return self.element_repository.get(element_name, '') if element_name else ''

    @staticmethod
    def create_test_case_template(directory: str):
        """创建测试用例模板文件"""
        template_path = os.path.join(directory, 'test_case_template.xlsx')
        if not os.path.exists(template_path):
            df = pd.DataFrame(columns=[
                ExcelTestCase.COLUMN_CASE_ID,
                ExcelTestCase.COLUMN_CASE_NAME,
                ExcelTestCase.COLUMN_ACTION,
                ExcelTestCase.COLUMN_ELEMENT,
                ExcelTestCase.COLUMN_PRIORITY,
                ExcelTestCase.COLUMN_EXPECT,
                ExcelTestCase.COLUMN_SKIP,
                ExcelTestCase.COLUMN_VALUE
            ])
            df.to_excel(template_path, index=False)
            logger.debug(f"创建测试用例模板文件: {template_path}")
        else:
            logger.debug(f"测试用例模板文件已存在: {template_path}")


def get_excel_files(directory: str) -> List[Path]:
    """使用 pathlib.Path 获取目录下所有的Excel文件（排除临时文件）"""
    logger.info(f"搜索目录: {directory}")
    excel_files = []
    dir_path = Path(directory)
    if not dir_path.is_dir():
        logger.error(f"指定的路径 {directory} 不是一个有效的目录")
        return excel_files
    for file in dir_path.glob("*"):
        if file.is_file() and file.suffix == '.xlsx' and not file.name.startswith('~$'):
            excel_files.append(file)
            logger.debug(f"找到Excel文件: {file}")
    return excel_files
