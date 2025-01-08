import os
from typing import Dict, Any

import yaml


class YamlHandler:
    @staticmethod
    def load_yaml(file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"YAML文件不存在: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise Exception(f"YAML文件解析错误: {str(e)}")
