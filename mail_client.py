import smtplib
from email.message import EmailMessage

# 构造邮件内容
msg = EmailMessage()
msg.set_content("你好！这是一封来自本地测试脚本的邮件。\n欢迎使用 Python 邮件服务器！")
msg['Subject'] = "Python SMTP 测试"
msg['From'] = "sender@example.com"
msg['To'] = "receiver@example.com"

# 连接到我们刚才搭建的本地服务器
# 指定 IP 和 端口 (1025)
try:
    with smtplib.SMTP('127.0.0.1', 1025) as server:
        server.send_message(msg)
        print("邮件发送成功！")
except ConnectionRefusedError:
    print("连接失败！请确保你的 mail_server.py 正在运行。")