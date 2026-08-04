根据Nodeseek [n18255447846](https://www.nodeseek.com/space/19052) 的帖子[免费+503萨尔瓦多eSIM号码激活教程（脚本）](https://www.nodeseek.com/post-855726-1) 逆向结果二次开发

脚本内容由AI生成

![image](https://github.com/qingqiu66/tigo/blob/main/image.png)


# 脚本

安装requirements.txt中的依赖包
```
pip3 install -r requirements.txt
```
运行main.py
```
py main.py 89503... [ICCID]
```

---

# BOT
# 🤖 Tigo SIM 自动化激活 Telegram Bot

基于 Python 开发的 Telegram 机器人，支持通过 Telegram 消息自动调用 Tigo 接口完成 SIM 卡/eSIM 的激活流程，并内置了萨尔瓦多 DUI 身份凭证的校验码自动生成算法。

---

## ✨ 核心特性

- **📱 智能卡号识别**：支持直接粘贴以 `89503` 开头的 ICCID 卡号快速提交激活。
- **💬 多指令交互**：保留传统的 `/iccid` 指令触发方式，并支持 `/esim` 一键获取二维码与 LPA 激活码。
- **🆔 智能身份生成**：内置符合萨尔瓦多官方校验规则的 DUI 算法，自动匹配合规身份信息提交激活。
- **⚡ 一键自动化部署**：提供 `start.sh` 部署脚本，自动识别 Linux 发行版、安装 Python 环境、挂载 Systemd 守护进程与开机自启。

---

## 📁 目录结构

部署前请确保项目根目录下包含以下核心文件：

- bot.py （Telegram Bot 主程序）
- start.sh （自动化环境检查与部署脚本）
- qr.png （eSIM 激活二维码图片）
- .env （可选配置文件，存放 Bot Token）
- README.md （说明文档）

---

## 🚀 快速部署指南

推荐使用包含 root 权限的 Linux 服务器（支持 Ubuntu, Debian, CentOS, AlmaLinux, Rocky Linux 等）。

### 1. 打包上传并解压

将所有文件打包为 `bot.zip` 并上传至服务器，然后执行解压：

UNZIP 方式解压:
unzip bot.zip -d tigo-bot && cd tigo-bot

Python 模块解压:
python3 -m zipfile -e bot.zip ./tigo-bot && cd tigo-bot

### 2. 运行一键部署脚本

为 `start.sh` 赋予执行权限并以 Bash 运行：

chmod +x start.sh
bash start.sh

start.sh 脚本会自动完成以下操作：
1. 检测并自动安装 python3、pip3 及相关依赖包（python-telegram-bot, requests, faker, python-dotenv）。
2. 检测是否存在 .env 文件。若不存在，会提示输入 Telegram Bot Token 并自动创建。
3. 自动清理旧的 Webhook 设置（确保 Bot 切换至轮询模式）。
4. 注册 tigobot.service 到 Systemd，实现后台常驻与开机自启。

---

## 🛠️ 运维与服务管理

部署完成后，Bot 将在后台自动运行。你可以通过以下命令进行维护：

查看服务运行状态:
systemctl status tigobot

查看实时运行日志:
journalctl -u tigobot -f

重启服务:
systemctl restart tigobot

停止服务:
systemctl stop tigobot

---

## 📖 Telegram 指令与使用说明

直接发送卡号 (8950303031005284838):
推荐用法。直接发送 18-20 位以 89503 开头的 ICCID，Bot 自动触发激活。

指令激活 (/iccid 8950303031005284838):
兼容指令格式激活。

获取 eSIM (/esim):
发送默认 eSIM 的二维码图片及 LPA 激活码。

帮助说明 (/start):
查看欢迎信息、支持的命令及免责声明。

注意：如果发送了不符合 89503 格式的纯数字或非法文本，机器人会自动给出格式错误提示或使用引导。

---

## ⚠️ 免责声明 (Disclaimer)

1. 软件用途：本项目仅供技术研究、软件测试及自动化接口验证使用，严禁用于任何商业用途或非法目的。
2. 数据说明：测试中用到的身份信息（DUI 等）均为伪随机算法自动生成，不含任何真实个人隐私。
3. 责任界定：使用者因误用或滥用本工具导致的任何后果均由使用者自行承担。