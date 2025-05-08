import requests


def requests_get(type_num, env=None):
    c_open_id = "_000PaWE7zmBN54NBCehAZh-AxaK7BU58wA9"  # _000MxS0ikIFT7k8o4TxZUU5WQvgkj08oU2c 李彦卿 _000PaWE7zmBN54NBCehAZh-AxaK7BU58wA9 冬雪 _000MEosMzoBJHqFie_LNyzOQfZxLndJ_h5_ 代丹
    data = {
        "test": {
            "bUserId": "9250",
            "Urm-Token-Sso": "dc64bcbc2ba54fd592490c39883a0937",
            "base_url": "http://live.mulan.autohome.com.cn/",
        },
        "pre": {
            "bUserId": "26789",  # 全球猎奇 41711 26789
            "Urm-Token-Sso": "dc64bcbc2ba54fd592490c39883a0937",
            "base_url": "http://live.thallo.autohome.com.cn/",
        },
    }
    params = {
        "bUserId": data.get(env).get("bUserId"),
        "cOpenId": c_open_id,
        "type": type_num,
    }
    headers = {
        "Urm-Token-Sso": data.get(env).get("Urm-Token-Sso"),
    }

    url = "/api/aim/data/clean"
    return requests.get(
        url=data.get(env).get("base_url") + url, headers=headers, params=params
    )


env = "pre"
types = [1, 2, 3, 5, 4]
type_num = 1

for type_num in types:
    res = requests_get(type_num, env)
    print(res.json())
