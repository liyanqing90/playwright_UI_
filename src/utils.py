import socket
import subprocess

from configobj import ConfigObj


def singleton(cls):
    _instance = {}

    def inner():
        if cls not in _instance:
            _instance[cls] = cls()
        return _instance[cls]

    return inner


def set_ini(key, value):
    config = ConfigObj("pytest.ini", encoding="UTF8")
    config["pytest"][key] = value
    config.write()


def get_ini(key):
    config = ConfigObj("pytest.ini", encoding="UTF8")
    return config["pytest"][key]


def save_info(project, env, reporter):
    reporter = (
        "Jenkins"
        if reporter == "jenkins"
        else subprocess.getoutput("git config user.name") or socket.gethostname()
    )
    config = ConfigObj("pytest.ini", encoding="UTF8")
    config["pytest"]["reporter"] = reporter
    config["pytest"]["project"] = project
    config["pytest"]["base_env"] = env
    config["pytest"]["testpaths"] = f"tests/{project}/case/"
    if env == "test":
        url = "magicdoor-test.com/"
    elif env == "online":
        url = "magicdoor.com/"
    config.write()
