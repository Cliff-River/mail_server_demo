import yagmail
import smtplib
import os
import io
import logging
from typing import Optional, List, Dict, Any, Tuple
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
    支持通过文件路径或字节流发送附件，无需解析文件内容。
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

    def _file_to_stream(self, file_path: str) -> io.BytesIO:
        """
        将文件转换为字节流，不解析文件内容

        Args:
            file_path: 文件路径

        Returns:
            BytesIO 对象，包含文件名属性

        Raises:
            FileNotFoundError: 文件不存在
            IOError: 文件读取失败
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"附件文件不存在: {file_path}")

        with open(file_path, 'rb') as f:
            stream = io.BytesIO(f.read())

        stream.name = os.path.basename(file_path)
        return stream

    def _prepare_attachments(
        self,
        attachments: Optional[List[str]] = None,
        byte_attachments: Optional[List[Tuple[str, bytes]]] = None,
    ) -> List[io.IOBase]:
        """
        准备附件数据，将文件路径和字节数据转换为字节流

        Args:
            attachments: 文件路径列表
            byte_attachments: 字节数据附件列表，格式为 [(filename, bytes), ...]

        Returns:
            统一格式的附件列表，每个元素为 io.BytesIO 对象
        """
        prepared = []

        if attachments:
            for file_path in attachments:
                prepared.append(self._file_to_stream(file_path))

        if byte_attachments:
            for filename, file_bytes in byte_attachments:
                stream = io.BytesIO(file_bytes)
                stream.name = filename
                prepared.append(stream)

        return prepared

    def send_email(
        self,
        to: List[str],
        subject: str,
        contents: Any,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        byte_attachments: Optional[List[Tuple[str, bytes]]] = None,
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
            byte_attachments: 字节数据附件列表，格式为 [(filename, bytes), ...]

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

        prepared_attachments = self._prepare_attachments(attachments, byte_attachments)

        try:
            result = self._client.send(
                to=to,
                subject=subject,
                contents=contents,
                cc=cc,
                bcc=bcc,
                attachments=prepared_attachments,
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
    byte_attachments: Optional[List[Tuple[str, bytes]]] = None,
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
        byte_attachments: 字节数据附件列表，格式为 [(filename, bytes), ...]
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
            byte_attachments=byte_attachments,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    report_content = """========================================
              系统状态报告
========================================
生成时间: 2026-07-26
报告类型: 自动生成

[服务器状态]
CPU 使用率: 23.5%
内存使用率: 67.2%
磁盘空间: 45.8 GB / 100 GB

[服务状态]
SMTP 服务: 运行中
HTTP 服务: 运行中
数据库连接: 正常

[告警信息]
无异常告警

========================================
报告结束
========================================
""".encode('utf-8')

    csv_content = """日期,用户数,邮件发送量,成功率
2026-07-20,1250,3500,98.5%
2026-07-21,1320,3800,99.1%
2026-07-22,1280,3600,98.8%
2026-07-23,1400,4100,99.2%
2026-07-24,1350,3900,98.9%
2026-07-25,1420,4200,99.3%
2026-07-26,1380,4000,99.0%
""".encode('utf-8')

    try:
        result = send_email_simple(
            to=["receiver@example.com"],
            subject="Python SMTP 身份验证测试 - 字节流附件",
            contents="这是一封使用字节流发送附件的邮件！\n\n附件内容为系统状态报告，由程序自动生成，未读取任何文件。",
            cc=["cc1@example.com", "cc2@example.com", "cc3@example.com"],
            byte_attachments=[("system_report.txt", report_content)],
        )
        print(result["message"])
    except AuthenticationError as e:
        print(f"发送失败：{e}")
    except SMTPError as e:
        print(f"SMTP 协议错误：{e}")
    except ConnectionError as e:
        print(f"连接失败：{e}")
    except MailError as e:
        print(f"邮件发送失败：{e}")

    try:
        byte_result = send_email_simple(
            to=["receiver@example.com"],
            subject="Python SMTP 身份验证测试 - 多附件发送",
            contents="这是一封包含多个字节流附件的邮件！\n\n附件内容均由程序自动生成，未访问文件系统。",
            cc=["cc1@example.com"],
            byte_attachments=[
                ("system_report.txt", report_content),
                ("daily_stats.csv", csv_content),
            ],
        )
        print(byte_result["message"])
    except AuthenticationError as e:
        print(f"发送失败：{e}")
    except SMTPError as e:
        print(f"SMTP 协议错误：{e}")
    except ConnectionError as e:
        print(f"连接失败：{e}")
    except MailError as e:
        print(f"邮件发送失败：{e}")