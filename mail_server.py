import time
from aiosmtpd.controller import Controller
from email import message_from_bytes
from typing import Any
from aiosmtpd.smtp import SMTP, Session, Envelope, AuthResult, LoginPassword


class ModernSession(Session):
    @property
    def login_data(self):
        return self._login_data


    @login_data.setter
    def login_data(self, value):
        self._login_data = value


class ModernSMTP(SMTP):
    def _create_session(self) -> Session:
        return ModernSession(self.loop)


class ModernController(Controller):
    def factory(self):
        return ModernSMTP(self.handler, **self.SMTP_kwargs)

# 定义一个身份验证器函数
def my_authenticator(
    server: SMTP, 
    session: Session, 
    envelope: Envelope, 
    mechanism: str, 
    auth_data: Any
) -> AuthResult:
    # 确保使用的是常见的 LOGIN 或 PLAIN 机制
    if mechanism not in ('LOGIN', 'PLAIN'):
        return AuthResult(success=False, handled=False)
        
    # 确保框架成功解析出了用户名和密码对象
    if not isinstance(auth_data, LoginPassword):
        return AuthResult(success=False, handled=False)

    # 提取用户名和密码（注意这里是 bytes 类型，需要解码或者直接对比字节）
    username = auth_data.login
    password = auth_data.password

    # 2. 核心校验逻辑（这里写死账密用于演示，实际中应查询数据库）
    if username == b'admin@example.com' and password == b'secret123':
        print(f"[*] 身份验证成功: 用户 {username.decode('utf-8')} 已登录。")
        return AuthResult(success=True)
        
    print(f"[!] 身份验证被拒绝: 用户 {username.decode('utf-8')} 密码错误。")
    return AuthResult(success=False, handled=False)

class CustomMailHandler:
    async def handle_DATA(self, server : SMTP, session : Session, envelope : Envelope):
        # envelope 包含了发件人、收件人和邮件原始数据
        print("== 收到新邮件 ==")
        print(f"发件人: {envelope.mail_from}")
        print(f"收件人: {envelope.rcpt_tos}")
        
        # 将字节流转换为 email.message.Message 对象以便于读取
        msg = message_from_bytes(envelope.content)
        
        # 打印邮件主题
        print(f"主题: {msg.get('Subject', '无主题')}")
        
        # 提取并打印邮件正文
        print("正文内容:")
        if msg.is_multipart():
            for part in msg.walk():
                # 只提取纯文本部分
                if part.get_content_type() == 'text/plain':
                    print(part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8'))
        else:
            print(msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8'))
            
        print("================\n")
        
        # 返回 250 状态码，告诉发送方邮件已成功接收
        return '250 Message accepted for delivery'

if __name__ == '__main__':
    # 初始化处理器
    handler = CustomMailHandler()
    
    # 设置控制器监听本地的 1025 端口
    # 注意：标准 SMTP 端口是 25，但在 Linux/Mac 上绑定 25 端口需要 root 权限，
    # 所以测试时通常使用 1025 或 8025。
    controller = ModernController(
        handler, 
        hostname='127.0.0.1', 
        port=1025,
        authenticator=my_authenticator, # 传入验证器
        auth_require_tls=False,         # 允许在非加密连接下发送密码（仅限本地测试使用！）
        auth_required=True              # 拒绝所有未提供正确账密的发件请求
    )
    
    # 启动服务器
    controller.start()
    print("SMTP 服务器已启动，正在监听 127.0.0.1:1025 ...")
    print("按 Ctrl+C 停止服务器。")
    
    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n检测到 Ctrl+C，服务器正在关闭...")
    finally:
        controller.stop()