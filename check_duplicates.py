from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

from utils.yaml_handler import YamlHandler
from utils.logger import logger


def get_line_number(content: str, target: str) -> int:
    """获取目标字符串在内容中的行号"""
    for i, line in enumerate(content.splitlines(), 1):
        if target in line:
            return i
    return 0


def format_duplicate_locations(locations: List[Tuple[Path, int]]) -> str:
    """格式化重复位置信息"""
    if len(locations) == 2:
        file1, line1 = locations[0]
        file2, line2 = locations[1]
        return f"{file1.name} 第{line1}行和 {file2.name} 第{line2}行重复"
    else:
        # 处理超过两个重复的情况
        parts = []
        for file_path, line in locations:
            parts.append(f"{file_path.name} 第{line}行")
        return "、".join(parts) + "重复"


def check_cases_duplicates(cases_dir: Path) -> Dict[str, List[Tuple[Path, int]]]:
    """检查cases目录下的用例名称重复"""
    duplicates = defaultdict(list)
    case_names = defaultdict(list)
    yaml_handler = YamlHandler()

    for yaml_file in cases_dir.glob("**/*.yaml"):
        content = yaml_handler.load_yaml(yaml_file)
        with open(yaml_file, "r", encoding="utf-8") as f:
            file_content = f.read()

        if isinstance(content, dict) and "test_cases" in content:
            for case in content["test_cases"]:
                if "name" in case:
                    case_name = case["name"]
                    line_number = get_line_number(file_content, case_name)
                    case_names[case_name].append((yaml_file, line_number))

    # 找出重复的用例名
    for name, locations in case_names.items():
        if len(locations) > 1:
            duplicates[name] = locations

    return duplicates


def check_data_duplicates(data_dir: Path) -> Dict[str, List[Tuple[Path, int]]]:
    """检查data目录下的测试数据用例名称重复"""
    duplicates = defaultdict(list)
    test_data_names = defaultdict(list)
    yaml_handler = YamlHandler()

    for yaml_file in data_dir.glob("**/*.yaml"):
        content = yaml_handler.load_yaml(yaml_file)
        with open(yaml_file, "r", encoding="utf-8") as f:
            file_content = f.read()

        if isinstance(content, dict) and "test_data" in content:
            for test_name in content["test_data"].keys():
                line_number = get_line_number(file_content, test_name)
                test_data_names[test_name].append((yaml_file, line_number))

    # 找出重复的测试数据名称
    for name, locations in test_data_names.items():
        if len(locations) > 1:
            duplicates[name] = locations

    return duplicates


def check_elements_duplicates(elements_dir: Path) -> Dict[str, List[Tuple[Path, int]]]:
    """检查elements目录下的元素名称重复"""
    duplicates = defaultdict(list)
    element_names = defaultdict(list)
    yaml_handler = YamlHandler()

    for yaml_file in elements_dir.glob("**/*.yaml"):
        content = yaml_handler.load_yaml(yaml_file)
        with open(yaml_file, "r", encoding="utf-8") as f:
            file_content = f.read()

        if isinstance(content, dict) and "elements" in content:
            for element_name in content["elements"].keys():
                line_number = get_line_number(file_content, element_name)
                element_names[element_name].append((yaml_file, line_number))

    # 找出重复的元素名称
    for name, locations in element_names.items():
        if len(locations) > 1:
            duplicates[name] = locations

    return duplicates


def check_project_duplicates(project_dir: Path) -> bool:
    """检查单个项目内的重复项，返回是否有重复项"""
    project_name = project_dir.name
    has_duplicates = False
    project_has_duplicates = False

    # 检查cases目录
    cases_dir = project_dir / "cases"
    if cases_dir.exists():
        case_duplicates = check_cases_duplicates(cases_dir)
        if case_duplicates:
            has_duplicates = True
            project_has_duplicates = True
            logger.info(f"\n{project_name} 项目中发现重复的用例名称：")
            for name, locations in case_duplicates.items():
                logger.info(f'"{name}" 在 {format_duplicate_locations(locations)}')

    # 检查data目录
    data_dir = project_dir / "data"
    if data_dir.exists():
        data_duplicates = check_data_duplicates(data_dir)
        if data_duplicates:
            has_duplicates = True
            project_has_duplicates = True
            logger.info(f"\n{project_name} 项目中发现重复的测试数据名称：")
            for name, locations in data_duplicates.items():
                logger.info(f'"{name}" 在 {format_duplicate_locations(locations)}')

    # 检查elements目录
    elements_dir = project_dir / "elements"
    if elements_dir.exists():
        element_duplicates = check_elements_duplicates(elements_dir)
        if element_duplicates:
            has_duplicates = True
            project_has_duplicates = True
            logger.info(f"\n{project_name} 项目中发现重复的元素名称：")
            for name, locations in element_duplicates.items():
                logger.info(f'"{name}" 在 {format_duplicate_locations(locations)}')

    return project_has_duplicates


def main():
    test_data_dir = Path("test_data")
    has_any_duplicates = False

    # 遍历test_data下的所有项目
    for project_dir in test_data_dir.iterdir():
        if not project_dir.is_dir():
            continue

        if check_project_duplicates(project_dir):
            has_any_duplicates = True

    if not has_any_duplicates:
        logger.info("\n所有项目中均未发现重复项")


if __name__ == "__main__":
    main()
