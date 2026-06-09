import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

# 创建带附件的邮件
msg = MIMEMultipart()
msg['Subject'] = "Python SMTP 身份验证测试 - 带附件"
msg['From'] = "admin@example.com"
msg['To'] = "receiver@example.com"
# 添加多个抄送地址
msg['Cc'] = "cc1@example.com, cc2@example.com, cc3@example.com"

# 添加邮件正文
body = "这是一封经过密码验证才发送成功的邮件！\n\n附件已包含在内。"
msg.attach(MIMEText(body, 'plain', 'utf-8'))

# 添加附件
def add_attachment(message, file_path):
    if os.path.exists(file_path):
        filename = os.path.basename(file_path)
        # 创建 MIMEBase 对象
        part = MIMEBase('application', 'octet-stream')
        with open(file_path, 'rb') as file:
            part.set_payload(file.read())
        # 编码
        encoders.encode_base64(part)
        # 添加头信息
        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        message.attach(part)
        print(f"已添加附件: {filename}")
    else:
        print(f"警告：附件文件 {file_path} 不存在，已跳过")

# 添加示例附件（如果文件存在）
add_attachment(msg, 'example.txt')

try:
    with smtplib.SMTP('127.0.0.1', 1025) as server:
        # 新增：调用 login 方法提供账号和密码
        server.login('admin@example.com', 'secret123')
        
        # 获取所有收件人（包括抄送）
        from_addr = msg['From']
        to_addrs = [addr.strip() for addr in msg['To'].split(',')]
        cc_addrs = [addr.strip() for addr in msg['Cc'].split(',')] if msg['Cc'] else []
        all_recipients = to_addrs + cc_addrs
        
        server.sendmail(from_addr, all_recipients, msg.as_string())
        print("邮件发送成功！")
        
except smtplib.SMTPAuthenticationError:
    print("发送失败：账号或密码错误！")
except smtplib.SMTPException as e:
    print(f"SMTP 协议发生错误：{e}")
except ConnectionRefusedError:
    print("连接失败！请确保你的 mail_server.py 正在运行。")