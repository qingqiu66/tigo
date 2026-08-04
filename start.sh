#!/bin/bash

# ==========================================
# Tigo Bot 一键部署与自动化环境配置脚本
# ==========================================

# 确保脚本遇到致命错误时退出
set -e

# 获取脚本所在绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CD_PATH="$SCRIPT_DIR"
PYTHON_SCRIPT="$SCRIPT_DIR/bot.py"
SERVICE_NAME="tigobot"

echo "=========================================="
echo "🚀 开始检查并配置 Tigo Bot 运行环境..."
echo "=========================================="

# 1. 检查 root 权限 (Systemd 服务配置需要 root)
if [ "$EUID" -ne 0 ]; then
  echo "❌ 请使用 root 权限运行此脚本！(例如: sudo bash start.sh)"
  exit 1
fi

# 2. 检测并安装 Python3 & pip
echo "🔍 检查 Python3 与 pip3 安装状态..."

install_packages() {
    if command -v apt-get &> /dev/null; then
        echo "📦 检测到 apt 包管理器，正在更新并安装 Python3..."
        apt-get update -y
        apt-get install -y python3 python3-pip python3-venv curl
    elif command -v dnf &> /dev/null; then
        echo "📦 检测到 dnf 包管理器，正在安装 Python3..."
        dnf install -y python3 python3-pip curl
    elif command -v yum &> /dev/null; then
        echo "📦 检测到 yum 包管理器，正在安装 Python3..."
        yum install -y python3 python3-pip curl
    else
        echo "❌ 未能识别系统包管理器，请手动安装 Python3 和 pip3 后重试。"
        exit 1
    fi
}

if ! command -v python3 &> /dev/null || ! command -v pip3 &> /dev/null; then
    echo "⚠️ 未检测到完整的 Python3 或 pip3，准备自动安装..."
    install_packages
else
    echo "✅ Python3 和 pip3 已安装。"
fi

# 3. 检测并安装依赖库
echo "🔍 检查 Python 依赖库..."

REQUIRED_PACKAGES=("python-telegram-bot" "requests" "faker" "python-dotenv")

for pkg in "${REQUIRED_PACKAGES[@]}"; do
    # python-telegram-bot 的导入名称在 python 里是 telegram
    import_name="$pkg"
    if [ "$pkg" == "python-telegram-bot" ]; then
        import_name="telegram"
    elif [ "$pkg" == "python-dotenv" ]; then
        import_name="dotenv"
    fi

    if ! python3 -c "import $import_name" &> /dev/null; then
        echo "⏳ 正在自动安装依赖: $pkg ..."
        # 兼容部分 Linux 系统的 break-system-packages 限制
        python3 -m pip install "$pkg" --break-system-packages &> /dev/null || python3 -m pip install "$pkg"
    else
        echo "  - $pkg: 已安装"
    fi
done
echo "✅ 所有 Python 依赖库检测并就绪！"

# 4. 检查必要配置文件
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "⚠️ 未在项目目录下找到 .env 文件！"
    read -p "请输入你的 Telegram BOT_TOKEN: " input_token
    if [ -n "$input_token" ]; then
        echo "BOT_TOKEN=$input_token" > "$SCRIPT_DIR/.env"
        echo "✅ .env 文件已生成！"
    else
        echo "❌ 未提供 BOT_TOKEN，脚本退出。"
        exit 1
    fi
fi

# 5. 自动清理 Telegram 旧 Webhook (防止之前设置的 CF Webhook 干扰)
echo "🧹 尝试清理 Telegram 旧 Webhook 设置..."
BOT_TOKEN=$(grep -E '^BOT_TOKEN=' "$SCRIPT_DIR/.env" | cut -d '=' -f2- | tr -d '"' | tr -d "'")
if [ -n "$BOT_TOKEN" ]; then
    curl -s "https://api.telegram.org/bot${BOT_TOKEN}/deleteWebhook" > /dev/null
    echo "✅ Webhook 清理完成，已切换为轮询模式。"
fi

# 6. 配置 Systemd 开机自启服务
echo "⚙️ 正在配置 Systemd 服务 ($SERVICE_NAME.service)..."

PYTHON_BIN=$(which python3)

cat <<EOF > /etc/systemd/system/${SERVICE_NAME}.service
[Unit]
Description=Tigo Telegram Activation Bot Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${CD_PATH}
ExecStart=${PYTHON_BIN} ${PYTHON_SCRIPT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 7. 重载配置并启动服务
echo "🔄 重载 Systemd 进程并启动服务..."
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl restart ${SERVICE_NAME}

echo "=========================================="
echo "🎉 部署完成！Bot 已在后台运行并开启自启。"
echo "=========================================="
echo "💡 常用管理命令："
echo "  • 查看服务运行状态: systemctl status $SERVICE_NAME"
echo "  • 查看实时日志:     journalctl -u $SERVICE_NAME -f"
echo "  • 重启 Bot:         systemctl restart $SERVICE_NAME"
echo "  • 停止 Bot:         systemctl stop $SERVICE_NAME"
echo "=========================================="