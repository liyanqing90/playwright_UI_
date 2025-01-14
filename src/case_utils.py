from src.load_data import DataConverter
from utils.config import DirPath


def run_test_data():
    data_merger = DataConverter(DirPath().test_dir)
    data = data_merger.convert_excel_data()

    return data
