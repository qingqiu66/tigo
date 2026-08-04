import sys
import uuid
import json
import random
import requests
from faker import Faker

fake = Faker("es_MX")

# ANSI 颜色定义 (终端高亮)
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


# =========================
# 萨尔瓦多 DUI 算法生成器
# =========================

def generate_dui():
    """生成合规的萨尔瓦多 DUI 9位纯数字 (带加权校验码)"""
    digits = [random.randint(0, 9) for _ in range(8)]
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    total_sum = sum(d * w for d, w in zip(digits, weights))
    
    remainder = total_sum % 10
    check_digit = 0 if remainder == 0 else 10 - remainder
    
    digits_str = "".join(map(str, digits))
    return f"{digits_str}{check_digit}"


# =========================
# 随机生成 Customer
# =========================

def generate_customer():
    gender_choice = random.choice(["M", "F"])

    if gender_choice == "M":
        first_name = fake.first_name_male()
        second_name = fake.first_name_male()
    else:
        first_name = fake.first_name_female()
        second_name = fake.first_name_female()

    surname = fake.last_name()

    return {
        "first_name": first_name.replace(" ", ""),
        "second_name": second_name.replace(" ", ""),
        "surname": surname.replace(" ", ""),
        "second_surname": "",
        "dob": fake.date_of_birth(minimum_age=20, maximum_age=40).isoformat(),
        "identification": generate_dui(),
        "identification_type": "DUI",
        "gender": None,
        "identification_issue_date": None,
        "identification_exp_date": None,
        "email": None,
        "contact_phone_number": None,
        "address": {
            "state": "SANTA ANA",
            "city": "SANTA ANA"
        },
        "nationality": None,
        "manual_input": False
    }


# =========================
# API 请求包装
# =========================

def api(url, opts=None):
    if opts is None:
        opts = {}

    headers = opts.get("headers", {})
    headers["referer"] = "https://activate.tigo.com.sv/"

    base_url = "https://activate-sv-xapis-prod.tigocloud.net/sv"
    
    response = requests.request(
        method=opts.get("method", "GET"),
        url=base_url + url,
        headers=headers,
        data=opts.get("body")
    )

    try:
        result_json = response.json()
    except Exception:
        print(f"\n{RED}[✘] 响应错误: 目标服务器返回非 JSON 数据{RESET}")
        raise Exception("Invalid JSON response")

    response_data = result_json.get("response", {})
    result = response_data.get("result", {})

    if result.get("code") != 200:
        error_msg = result.get("result_message", {}).get("value", "Unknown error")
        print(f"\n{RED}┌──────────────────────────────────────────┐{RESET}")
        print(f"{RED}│             API 请求异常 (ERROR)         │{RESET}")
        print(f"{RED}├──────────────────────────────────────────┤{RESET}")
        print(f"{RED}│ Code: {result.get('code')}                         │{RESET}")
        print(f"{RED}│ Message: {error_msg:<31} │{RESET}")
        print(f"{RED}└──────────────────────────────────────────┘{RESET}")
        raise Exception(error_msg)

    return response_data.get("data")


# =========================
# 主程序
# =========================

def main():
    if len(sys.argv) < 2:
        print(f"{YELLOW}Usage: py main.py <ICCID>{RESET}")
        return

    iccid = sys.argv[1]
    request_id = str(uuid.uuid4())

    print(f"\n{CYAN}=========================================={RESET}")
    print(f"{CYAN}  Tigo SIM 激活自动化工具 (SV)            {RESET}")
    print(f"{CYAN}=========================================={RESET}")
    print(f"[{BOLD}*{RESET}] 正在查询 SIM 卡卡号 (ICCID): {BOLD}{iccid}{RESET}")

    # 1. 查询 SIM 卡信息
    auth_data = api(
        f"/get-simcard?serialNumber={iccid}&requestId={request_id}&type=chip"
    )

    query_msisdn = auth_data["msisdn"]["value"]
    print(f"[{GREEN}✓{RESET}] 查询成功 | 初始 MSISDN: {BOLD}{query_msisdn}{RESET}")

    # 2. 生成 Customer 身份数据
    customer = generate_customer()
    full_name = f"{customer['first_name']} {customer['second_name']} {customer['surname']}".strip()
    dui_val = customer['identification']
    
    print(f"[{GREEN}✓{RESET}] 身份数据生成成功:")
    print(f"    ├─ 姓名: {BOLD}{full_name}{RESET}")
    print(f"    ├─ DUI 验证码: {BOLD}{dui_val}{RESET} (校验通过)")
    print(f"    └─ 出生日期: {customer['dob']}")

    # 3. 构造 Payload
    order_info = {
        "customer": customer,
        "activation": [
            {
                "offer": {},
                "offer_device": {},
                "resources": [
                    {
                        "parameters": [
                            {"name": "model"},
                            {"name": "imei"},
                            {"name": "icc", "value": iccid},
                            {"name": "msisdn", "value": query_msisdn},
                            {"name": "request_id", "value": request_id}
                        ]
                    }
                ]
            }
        ],
        "order": {
            "reference_number": "",
            "date": "",
            "action": "PREPAID_ACTIVATION",
            "journey": "activation"
        }
    }

    # 静默保存后台调式数据（不直接打到屏幕上）
    with open("last_order.json", "w", encoding="utf-8") as f:
        json.dump(order_info, f, indent=2, ensure_ascii=False)

    print(f"[{BOLD}*{RESET}] 正在提交激活请求...")

    # 4. 提交订单
    order = api(
        "/activation/order",
        {
            "method": "POST",
            "headers": {
                "content-type": "application/json",
                "authorization": f"Bearer {auth_data['accessToken']['value']}"
            },
            "body": json.dumps(order_info, ensure_ascii=False)
        }
    )

    # 5. 解析并格式化打印结果
    activated_msisdn = order["activation"]["attributes"]["resources"]["attributes"]["parameters"]["attributes"]["msisdn"]["value"]
    trans_id = order.get("transaction_id", {}).get("value", "N/A")

    print(f"\n{GREEN}┌──────────────────────────────────────────┐{RESET}")
    print(f"{GREEN}│           🎉 SIM 卡激活成功！            │{RESET}")
    print(f"{GREEN}├──────────────────────────────────────────┤{RESET}")
    print(f"{GREEN}│{RESET} {BOLD}激活手机号 (MSISDN):{RESET} {YELLOW}{activated_msisdn:<19}{RESET} {GREEN}│{RESET}")
    print(f"{GREEN}│{RESET} 绑定卡号 (ICCID):    {iccid:<19} {GREEN}│{RESET}")
    print(f"{GREEN}│{RESET} 使用 DUI 身份号:     {dui_val:<19} {GREEN}│{RESET}")
    print(f"{GREEN}│{RESET} 交易 ID:             {trans_id[:18]}... {GREEN}│{RESET}")
    print(f"{GREEN}└──────────────────────────────────────────┘{RESET}\n")


if __name__ == "__main__":
    main()