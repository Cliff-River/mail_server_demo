from typing import Any
from aiosmtpd.smtp import SMTP, Session, Envelope, AuthResult, LoginPassword
from config import VALID_CREDENTIALS


def my_authenticator(
    server: SMTP,
    session: Session,
    envelope: Envelope,
    mechanism: str,
    auth_data: Any
) -> AuthResult:
    if mechanism not in ('LOGIN', 'PLAIN'):
        return AuthResult(success=False, handled=False)

    if not isinstance(auth_data, LoginPassword):
        return AuthResult(success=False, handled=False)

    username = auth_data.login
    password = auth_data.password

    if username in VALID_CREDENTIALS and VALID_CREDENTIALS[username] == password:
        print(f"[*] 身份验证成功: 用户 {username.decode('utf-8')} 已登录。")
        return AuthResult(success=True)

    print(f"[!] 身份验证被拒绝: 用户 {username.decode('utf-8')} 密码错误。")
    return AuthResult(success=False, handled=False)