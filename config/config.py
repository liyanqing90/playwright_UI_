import os
from pathlib import Path


class DirPath:
    def __init__(self):
        self.test_dir = os.environ['TEST_DATA_DIR']
        self.base_dir = Path.cwd()
