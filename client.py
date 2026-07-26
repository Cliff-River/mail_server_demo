import yagmail
import smtplib
import os
import logging
from typing import Optional, List, Dict, Any
from config import HOSTNAME, PORT, VALID_CREDENTIALS

logger = logging.getLogger(__name__)


class MailError(Exception):
    """邮件发送相关错误的基类"""
    pass


class AuthenticationError(MailError):
    """SMTP身份验证失败错误"""
    pass


class SMTPError(MailError):
    """SMTP协议相关错误"""
    pass


class MailClient:
    """
    邮件客户端类，使用 yagmail 库实现邮件发送功能

    支持邮件主题、正文、抄送、密送和附件等功能，提供上下文管理器支持。
    """

    def __init__(
        self,
        smtp_host: str = HOSTNAME,
        smtp_port: int = PORT,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = False,
        use_ssl: bool = False,
    ) -> None:
        """
        初始化邮件客户端

        Args:
            smtp_host: SMTP服务器地址，默认为配置文件中的HOSTNAME
            smtp_port: SMTP服务器端口，默认为配置文件中的PORT
            username: SMTP用户名（邮箱地址）
            password: SMTP密码或授权码
            use_tls: 是否启用TLS加密
            use_ssl: 是否启用SSL加密
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self._client: Optional[yagmail.SMTP] = None

    def connect(self) -> None:
        """
        建立与SMTP服务器的连接

        Raises:
            ConnectionError: 连接失败时抛出
        """
        try:
            self._client = yagmail.SMTP(
                user=self.username,
                password=self.password,
                host=self.smtp_host,
                port=self.smtp_port,
                smtp_starttls=self.use_tls,
                smtp_ssl=self.use_ssl,
            )
        except Exception as e:
            raise ConnectionError(f"连接 SMTP 服务器失败: {str(e)}") from e

    def disconnect(self) -> None:
        """断开与SMTP服务器的连接"""
        if self._client is not None:
            try:
                self._client.close()
            except Exception as e:
                logger.warning(f"关闭SMTP连接时发生错误: {str(e)}")
            finally:
                self._client = None

    def send_email(
        self,
        to: List[str],
        subject: str,
        contents: Any,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        发送邮件

        Args:
            to: 收件人邮箱地址列表
            subject: 邮件主题
            contents: 邮件内容，可以是字符串、HTML字符串或内容列表
            cc: 抄送邮箱地址列表
            bcc: 密送邮箱地址列表
            attachments: 附件文件路径列表

        Returns:
            包含发送结果的字典，格式为 {"success": bool, "result": Any, "message": str}

        Raises:
            RuntimeError: 未建立连接时调用此方法
            ValueError: 收件人或主题为空
            FileNotFoundError: 附件文件不存在
            AuthenticationError: SMTP身份验证失败
            SMTPError: SMTP协议错误
            MailError: 其他邮件发送错误
        """
        if self._client is None:
            raise RuntimeError("请先调用 connect() 方法建立连接")

        if not to:
            raise ValueError("收件人列表不能为空")

        if not subject:
            raise ValueError("邮件主题不能为空")

        if attachments:
            for file_path in attachments:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"附件文件不存在: {file_path}")

        try:
            result = self._client.send(
                to=to,
                subject=subject,
                contents=contents,
                cc=cc,
                bcc=bcc,
                attachments=attachments,
            )
            return {"success": True, "result": result, "message": "邮件发送成功"}
        except smtplib.SMTPAuthenticationError as e:
            raise AuthenticationError(f"身份验证失败: {str(e)}") from e
        except smtplib.SMTPException as e:
            raise SMTPError(f"SMTP 协议错误: {str(e)}") from e
        except Exception as e:
            raise MailError(f"邮件发送失败: {str(e)}") from e

    def __enter__(self) -> "MailClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()


def get_default_credentials() -> Dict[str, str]:
    """
    获取默认的SMTP认证凭据

    Returns:
        包含用户名和密码的字典
    """
    return {
        k.decode('utf-8'): v.decode('utf-8')
        for k, v in VALID_CREDENTIALS.items()
    }


def send_email_simple(
    to: List[str],
    subject: str,
    contents: Any,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    attachments: Optional[List[str]] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    use_tls: bool = False,
    use_ssl: bool = False,
) -> Dict[str, Any]:
    """
    简化的邮件发送函数，自动处理连接和断开

    Args:
        to: 收件人邮箱地址列表
        subject: 邮件主题
        contents: 邮件内容
        cc: 抄送邮箱地址列表
        bcc: 密送邮箱地址列表
        attachments: 附件文件路径列表
        username: SMTP用户名，默认为配置文件中的默认凭据
        password: SMTP密码，默认为配置文件中的默认凭据
        smtp_host: SMTP服务器地址，默认为配置文件中的HOSTNAME
        smtp_port: SMTP服务器端口，默认为配置文件中的PORT
        use_tls: 是否启用TLS加密
        use_ssl: 是否启用SSL加密

    Returns:
        包含发送结果的字典
    """
    credentials = get_default_credentials()
    user = username or next(iter(credentials.keys()), None)
    pwd = password or credentials.get(user, None)
    host = smtp_host or HOSTNAME
    port = smtp_port or PORT

    with MailClient(
        smtp_host=host,
        smtp_port=port,
        username=user,
        password=pwd,
        use_tls=use_tls,
        use_ssl=use_ssl,
    ) as client:
        return client.send_email(
            to=to,
            subject=subject,
            contents=contents,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        result = send_email_simple(
            to=["receiver@example.com"],
            subject="Python SMTP 身份验证测试 - 带附件",
            contents="这是一封经过密码验证才发送成功的邮件！\n\n附件已包含在内。",
            cc=["cc1@example.com", "cc2@example.com", "cc3@example.com"],
            attachments=["example.txt"],
        )
        print(result["message"])
    except AuthenticationError as e:
        print(f"发送失败：{e}")
    except SMTPError as e:
        print(f"SMTP 协议错误：{e}")
    except ConnectionError as e:
        print(f"连接失败：{e}")
    except FileNotFoundError as e:
        print(f"附件错误：{e}")
    except MailError as e:
        print(f"邮件发送失败：{e}")