from src.load_data import LoadData
from src.utils import singleton
from utils.config import DirPath


@singleton
def run_test_data():
    data = LoadData(DirPath().test_dir).return_data()

    return data
