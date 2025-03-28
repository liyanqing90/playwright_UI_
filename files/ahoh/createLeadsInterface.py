import requests
import json


def login():
    """调用登录接口，获取 sso_token"""
    login_url = "http://auth.autohome.com.cn/api_urm_service/api/sso/open/login/login?mallTraceId=8444c3a35781e892&_appid=app_ahoh_app&_appVersion=&_h5Version="
    login_headers = {
        "Connection": "keep-alive",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Mobile Safari/537.36",
        "Host": "auth.autohome.com.cn"
    }
    login_data = {
        "account": "12500000002",
        "certificate": "Admin123!",
        "certificateType": 0,
        "productType": "product_ahoh",
        "appNo": "A00064"
    }

    try:
        login_response = requests.post(login_url, headers=login_headers, data=json.dumps(login_data))
        login_response.raise_for_status()  # 抛出 HTTPError 异常，以处理失败的状态码

        login_json = login_response.json()
        if login_json["returncode"] == 0:
            sso_token = login_json["result"]
            print("登录成功，获取到 sso_token:", sso_token)
            return sso_token
        else:
            print("登录失败:", login_json["message"])
            return None  # 返回 None 表示登录失败

    except requests.exceptions.RequestException as e:
        print("登录接口调用失败:", e)
        return None  # 返回 None 表示登录失败


def create_lead(sso_token):
    """调用创建线索接口"""
    create_lead_url = "http://ahohcrm.autohome.com.cn/api/ahohLeadTask/saveAppLeads?mallTraceId=077f666fe7fbd52d&_appid=app_ahoh_app&_appVersion=&_h5Version="
    create_lead_headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate",
        "accept-language": "zh-CN,zh;q=0.9",
        "connection": "keep-alive",
        "content-type": "application/json;charset=UTF-8",
        "host": "ahohcrm.autohome.com.cn",
        "origin": "http://app.ahohcrm.autohome.com.cn",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }
    create_lead_data = {
        "userNameEncrypt": "接口创建",
        "userPhoneEncrypt": "18210233933",
        "pvareaid": "6858691"
    }

    try:
        create_lead_headers["sso_token"] = sso_token  # 将 sso_token 添加到创建线索接口的请求头

        create_lead_response = requests.post(create_lead_url, headers=create_lead_headers,
                                             data=json.dumps(create_lead_data))
        create_lead_response.raise_for_status()  # 抛出 HTTPError 异常

        create_lead_json = create_lead_response.json()
        if create_lead_json["message"] == "success":
            print("创建线索成功:", create_lead_json)
            return True
        else:
            print("创建线索失败:", create_lead_json["message"])
            return False

    except requests.exceptions.RequestException as e:
        print("创建线索接口调用失败:", e)
        return False


def main():
    """主函数，用于调用登录接口和创建线索接口"""
    sso_token = login()
    if sso_token:
        create_lead(sso_token)
    else:
        print("未能获取 sso_token，无法创建线索。")


if __name__ == "__main__":
    main()  # 调用主函数
