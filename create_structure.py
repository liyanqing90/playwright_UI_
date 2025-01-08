import os
from pathlib import Path

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    directories = [
        'config',
        'page_objects',
        'test_cases',
        'test_scripts',
        'utils',
        'reports',
        'reports/allure-results',
        'logs'
    ]

    for directory in directories:
        Path(os.path.join(base_dir, directory)).mkdir(parents=True, exist_ok=True)
