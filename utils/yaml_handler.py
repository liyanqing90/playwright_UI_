import os
from pathlib import Path
from typing import Dict, Any, List

from ruamel.yaml import YAML

from utils.logger import logger


def get_yaml_files(directory: str) -> List[Path]:
    """使用 pathlib.Path 获取目录下所有的Excel文件（排除临时文件）"""
    logger.info(f"搜索目录: {directory}")
    yaml_files = []
    dir_path = Path(directory)
    if not dir_path.is_dir():
        logger.error(f"指定的路径 {directory} 不是一个有效的目录")
        return yaml_files
    yaml_files = [file for file in list(dir_path.glob("**/*.yaml"))]
    return yaml_files


class YamlHandler:
    def __init__(self):
        self.yaml = YAML(typ="safe")

    def load_yaml(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"YAML文件不存在: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            try:

                return self.yaml.load(f)
            except:
                raise Exception(f"YAML文件解析错误: ")

    def load_yaml_dir(self, file_path):
        yaml_files = get_yaml_files(file_path)
        all_data = []
        for yaml_file in yaml_files:
            all_data.append(self.load_yaml(yaml_file))

        result = {}
        for key in set(k for d in all_data for k in d.keys()):
            value = None  # 先初始化为 None
            for d in all_data:
                if key in d:  # 先判断键是否存在，避免 KeyError
                    if value is None:  # 根据值的类型初始化
                        if isinstance(d[key], list):
                            value = []
                        elif isinstance(d[key], dict):
                            value = {}
                        else:
                            value = d[key]  # 对于不是list和dict的，直接赋值
                            break  # 假设一个key的值都是同类型，若存在不是list和dict的，直接赋值，减少循环
                    if isinstance(d[key], list):
                        value += d[key]
                    elif isinstance(d[key], dict):
                        # 字典合并，如果需要复杂的合并逻辑，可以在这里修改
                        value.update(d[key])
                    elif isinstance(value, list):
                        value.append(d[key])  # 处理当key对应多个值，但是其中出现不是list或者dict的情况

            result[key] = value
        return result
