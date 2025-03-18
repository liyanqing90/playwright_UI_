import os
from pathlib import Path
from typing import Dict, Any

from ruamel.yaml import YAML

from utils.logger import logger


def get_yaml_files(directory: str) -> list[Any] | None:
    dir_path = Path(directory)
    if not dir_path.exists() or not dir_path.is_dir():
        logger.error(f"指定的路径 {directory} 不是一个有效的目录")
        return None
    yaml_files = [file for file in list(dir_path.glob("**/*.yaml"))]
    return yaml_files


class YamlHandler:
    def __init__(self):
        self.yaml = YAML(typ="safe")

    def load_yaml(self, file_path: Path) -> Dict[str, Any]:
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
        result = {}
        if not yaml_files:
            return result
        for yaml_file in yaml_files:
            all_data.append(self.load_yaml(yaml_file))
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

    def save_to_yaml(self, data_dict, output_dir, filename):
        """
        将字典写入 YAML 文件。

        Args:
            data_dict: 要写入的字典。
            output_dir: 输出目录的路径。
            filename: YAML 文件的名称（不含扩展名）。
        """

        self.yaml.indent(mapping=2, sequence=4, offset=2)  # 可选：设置 YAML 缩进样式
        self.yaml.preserve_quotes = True  # 可选: 保留引号
        self.yaml.default_flow_style = False  # 关键设置：禁用流式风格

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        filepath = Path(output_dir) / f"{filename}.yaml"
        # 检查目录是否存在，如果不存在则创建
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(filepath, 'w', encoding='utf-8') as f:
            self.yaml.dump(data_dict, f)
