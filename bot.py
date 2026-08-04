import os
import re
import uuid
import json
import random
import requests
from faker import Faker
from dotenv import load_dotenv

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# 加载 .env 环境变量
# =========================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("错误：未在 .env 文件中获取到 BOT_TOKEN，请检查配置！")

# 全局常量
LPA_CODE = "LPA:1$millicomelsalvador.validereachdpplus.com$GENERICJOWMI-FAHTCU0-SKFMYPW6UIEFGRWC8GE933ITFAUVN63WMUVHFOWTS80"
IMAGE_PATH = "qr.png"

fake = Faker("es_MX")

DISCLAIMER_TEXT = """
<b>⚠️ 免责声明 (Disclaimer)</b>

1. <b>软件用途</b>：本 Bot 仅供技术研究、软件测试及自动化接口验证使用。严禁用于任何商业用途或非法目的。
2. <b>数据说明</b>：测试中用到的身份信息（DUI 等）均为伪随机算法自动生成，不含任何真实个人隐私。
3. <b>责任界定</b>：使用者因误用或滥用本工具导致的任何后果均由使用者自行承担。
"""

# =========================
# 核心算法与 API 逻辑
# =========================

def generate_dui():
    """生成合规的萨尔瓦多 DUI 9位纯数字 (带加权校验码)"""
    digits = [random.randint(0, 9) for _ in range(8)]
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    total_sum = sum(d * w for d, w in zip(digits, weights))
    
    remainder = total_sum % 10
    check_digit = 0 if remainder == 0 else 10 - remainder
    
    return "".join(map(str, digits)) + str(check_digit)


def generate_customer():
    gender_choice = random.choice(["M", "F"])
    if gender_choice == "M":
        first_name = fake.first_name_male()
        second_name = fake.first_name_male()
    else:
        first_name = fake.first_name_female()
        second_name = fake.first_name_female()

    return {
        "first_name": first_name.replace(" ", ""),
        "second_name": second_name.replace(" ", ""),
        "surname": fake.last_name().replace(" ", ""),
        "second_surname": "",
        "dob": fake.date_of_birth(minimum_age=20, maximum_age=40).isoformat(),
        "identification": generate_dui(),
        "identification_type": "DUI",
        "gender": None,
        "identification_issue_date": None,
        "identification_exp_date": None,
        "email": None,
        "contact_phone_number": None,
        "address": {"state": "SANTA ANA", "city": "SANTA ANA"},
        "nationality": None,
        "manual_input": False
    }


def api_request(url, opts=None):
    if opts is None:
        opts = {}

    headers = opts.get("headers", {})
    headers["referer"] = "https://activate.tigo.com.sv/"
    base_url = "https://activate-sv-xapis-prod.tigocloud.net/sv"
    
    response = requests.request(
        method=opts.get("method", "GET"),
        url=base_url + url,
        headers=headers,
        data=opts.get("body"),
        timeout=15
    )

    try:
        result_json = response.json()
    except Exception:
        raise Exception(f"服务器返回非 JSON 响应 (HTTP Status: {response.status_code})")

    response_data = result_json.get("response", {})
    result = response_data.get("result", {})

    if result.get("code") != 200:
        error_msg = result.get("result_message", {}).get("value", "未知 API 错误")
        raise Exception(f"接口错误 [{result.get('code')}]: {error_msg}")

    return response_data.get("data")


def process_activation(iccid: str) -> dict:
    request_id = str(uuid.uuid4())

    auth_data = api_request(
        f"/get-simcard?serialNumber={iccid}&requestId={request_id}&type=chip"
    )
    query_msisdn = auth_data["msisdn"]["value"]

    customer = generate_customer()
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

    order = api_request(
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

    activated_msisdn = order["activation"]["attributes"]["resources"]["attributes"]["parameters"]["attributes"]["msisdn"]["value"]
    trans_id = order.get("transaction_id", {}).get("value", "N/A")

    return {
        "activated_msisdn": activated_msisdn,
        "trans_id": trans_id,
        "customer_name": f"{customer['first_name']} {customer['second_name']} {customer['surname']}",
        "dui": customer['identification']
    }


# =========================
# 通用激活逻辑封装
# =========================

async def handle_activation(update: Update, iccid: str):
    """处理 ICCID 激活的实际函数"""
    status_msg = await update.message.reply_text(
        f"⏳ 正在提交激活申请...\n<b>ICCID:</b> <code>{iccid}</code>",
        parse_mode=ParseMode.HTML
    )

    try:
        res = process_activation(iccid)
        success_text = (
            "🎉 <b>SIM 卡激活成功！</b>\n\n"
            f"📱 <b>激活手机号 (MSISDN):</b> <code>{res['activated_msisdn']}</code>\n"
            f"💳 <b>绑定 ICCID:</b> <code>{iccid}</code>\n"
            f"🆔 <b>使用生成 DUI:</b> <code>{res['dui']}</code>\n"
            f"👤 <b>分配姓名:</b> {res['customer_name']}\n"
            f"🔖 <b>交易 ID:</b> <code>{res['trans_id']}</code>"
        )
        await status_msg.edit_text(success_text, parse_mode=ParseMode.HTML)

    except Exception as e:
        error_text = (
            "💥 <b>激活失败！</b>\n\n"
            f"<b>ICCID:</b> <code>{iccid}</code>\n"
            f"<b>原因:</b> <code>{str(e)}</code>"
        )
        await status_msg.edit_text(error_text, parse_mode=ParseMode.HTML)


# =========================
# Telegram Bot 指令与消息回调
# =========================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "🤖 <b>欢迎使用 Tigo SIM 自动化激活测试 Bot</b>\n\n"
        "<b>📌 使用说明：</b>\n"
        "• <b>直接发送卡号</b>：发送以 <code>89503</code> 开头的 ICCID（如 <code>8950303031005284838</code>）直接激活\n"
        "• <code>/iccid [卡号]</code> - 兼容指令激活方式\n"
        "• <code>/esim</code> - 获取默认 eSIM 激活码与二维码\n\n"
        "-----------------------------------\n"
        f"{DISCLAIMER_TEXT}"
    )
    await update.message.reply_text(welcome_message, parse_mode=ParseMode.HTML)


async def iccid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ <b>参数缺失！</b>\n正确格式：<code>/iccid 89503xxxxxxxxx</code> 或直接发送卡号。",
            parse_mode=ParseMode.HTML
        )
        return

    iccid = context.args[0].strip()
    if not iccid.startswith("89503"):
        await update.message.reply_text(
            "❌ <b>ICCID 格式错误！</b>\n卡号必须以 <code>89503</code> 开头。",
            parse_mode=ParseMode.HTML
        )
        return

    await handle_activation(update, iccid)


async def esim_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption_text = (
        "📲 <b>eSIM 激活信息</b>\n\n"
        f"<b>LPA 激活码:</b>\n<code>{LPA_CODE}</code>\n\n"
        "💡 <i>可直接点击上述代码进行复制，或扫码添加。</i>"
    )

    if not os.path.exists(IMAGE_PATH):
        await update.message.reply_text(
            f"❌ 错误：找不到图片文件 <code>{IMAGE_PATH}</code>，请检查路径。",
            parse_mode=ParseMode.HTML
        )
        return

    with open(IMAGE_PATH, "rb") as photo_file:
        await update.message.reply_photo(
            photo=photo_file,
            caption=caption_text,
            parse_mode=ParseMode.HTML
        )


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理用户发送的所有普通文本消息"""
    raw_text = update.message.text.strip()

    # 1. 如果用户直接发送了以 89503 开头的纯数字（忽略中间可能夹带的空格或横杠）
    clean_iccid = re.sub(r"\D", "", raw_text) # 去除非数字字符

    if clean_iccid.startswith("89503") and len(clean_iccid) >= 18:
        await handle_activation(update, clean_iccid)
        return

    # 2. 如果输入了以 89 开头但不是 89503 开头，或者数字位数明显不对
    if clean_iccid.startswith("89") or raw_text.isdigit():
        await update.message.reply_text(
            "❌ <b>无效的 ICCID 卡号！</b>\n\n"
            "• Tigo ICCID 必须以 <code>89503</code> 开头（例如：<code>8950303031005284838</code>）\n"
            "• 请检查卡号输入是否有误。",
            parse_mode=ParseMode.HTML
        )
        return

    # 3. 其他非指令、非 ICCID 的无效文本输入提示
    invalid_hint = (
        "❓ <b>无法识别的输入或指令</b>\n\n"
        "<b>正确用法：</b>\n"
        "1. <b>直接发送卡号</b>：直接把以 <code>89503</code> 开头的 ICCID 发给我（例如 <code>8950303031005284838</code>）\n"
        "2. <b>获取 eSIM 信息</b>：发送 <code>/esim</code>\n"
        "3. <b>查看帮助说明</b>：发送 <code>/start</code>"
    )
    await update.message.reply_text(invalid_hint, parse_mode=ParseMode.HTML)


# =========================
# 程序主入口
# =========================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # 指令处理器
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("iccid", iccid_command))
    app.add_handler(CommandHandler("esim", esim_command))

    # 纯文本消息处理器（捕获所有普通聊天文本，放在 CommandHandler 之后）
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_message_handler))

    print("🤖 Telegram Bot 已成功启动并在后台轮询中...")
    app.run_polling()


if __name__ == "__main__":
    main()