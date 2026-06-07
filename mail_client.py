import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg.set_content("这是一封经过密码验证才发送成功的邮件！")
msg['Subject'] = "Python SMTP 身份验证测试"
msg['From'] = "admin@example.com"
msg['To'] = "receiver@example.com"

try:
    with smtplib.SMTP('127.0.0.1', 1025) as server:
        # 新增：调用 login 方法提供账号和密码
        server.login('admin@example.com', 'secret123')
        
        server.send_message(msg)
        print("邮件发送成功！")
        
except smtplib.SMTPAuthenticationError:
    print("发送失败：账号或密码错误！")
except smtplib.SMTPException as e:
    print(f"SMTP 协议发生错误：{e}")
except ConnectionRefusedError:
    print("连接失败！请确保你的 mail_server.py 正在运行。")