import logging
import base64
from typing import Dict, List, Any
from mailparser import MailParser
from aiosmtpd.smtp import SMTP, Session, Envelope
from utils.attachment import save_attachments

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EmailParser:
    def parse_from_bytes(self, content: bytes) -> Dict[str, Any]:
        try:
            parser = MailParser.from_bytes(content)
            return self._extract_email_data(parser)
        except Exception as e:
            raise EmailParseError(f"邮件解析失败: {str(e)}")

    def parse_from_string(self, content: str) -> Dict[str, Any]:
        try:
            parser = MailParser.from_string(content)
            return self._extract_email_data(parser)
        except Exception as e:
            raise EmailParseError(f"邮件解析失败: {str(e)}")

    def _extract_email_data(self, parser: MailParser) -> Dict[str, Any]:
        return {
            'from': self._extract_address_list(parser.from_),
            'to': self._extract_address_list(parser.to),
            'cc': self._extract_address_list(parser.cc),
            'bcc': self._extract_address_list(parser.bcc),
            'subject': parser.subject or '',
            'date': parser.date.isoformat() if parser.date else '',
            'timezone': str(parser.timezone) if parser.timezone else '',
            'message_id': parser.message_id or '',
            'reply_to': self._extract_address_list(parser.reply_to),
            'body': self._extract_body(parser),
            'attachments': self._extract_attachments_info(parser),
            'headers': dict(parser.headers) if parser.headers else {},
            'received': parser.received or [],
            'has_defects': parser.has_defects,
            'defects': parser.defects_categories if parser.defects else [],
        }

    def _extract_address_list(self, addresses) -> List[Dict[str, str]]:
        result = []
        if addresses:
            for item in addresses:
                name, address = item
                result.append({
                    'name': name or '',
                    'address': address or ''
                })
        return result

    def _extract_body(self, parser: MailParser) -> Dict[str, Any]:
        return {
            'plain': parser.text_plain or [],
            'html': parser.text_html or [],
            'full': parser.body or ''
        }

    def _extract_attachments_info(self, parser: MailParser) -> List[Dict[str, Any]]:
        result = []
        if parser.attachments:
            for attachment in parser.attachments:
                payload = attachment.get('payload', '')
                binary_data = b''
                if payload:
                    try:
                        binary_data = base64.b64decode(payload)
                    except Exception:
                        binary_data = payload.encode('utf-8', errors='replace')
                
                result.append({
                    'filename': attachment.get('filename', ''),
                    'size': len(binary_data),
                    'content_type': attachment.get('mail_content_type', ''),
                    'content_id': attachment.get('content-id', ''),
                    'encoding': attachment.get('content_transfer_encoding', ''),
                    'binary': binary_data
                })
        return result


class EmailParseError(Exception):
    pass


class CustomMailHandler:
    def __init__(self):
        self.email_parser = EmailParser()

    async def handle_DATA(self, server: SMTP, session: Session, envelope: Envelope):
        try:
            email_data = self.email_parser.parse_from_bytes(envelope.content)
            self._log_email_info(email_data)
            await save_attachments(email_data)
            return '250 Message accepted for delivery'
        except EmailParseError as e:
            logger.error(f"邮件解析错误: {e}")
            return '500 Internal server error'
        except Exception as e:
            logger.error(f"邮件处理异常: {e}")
            return '500 Internal server error'

    def _log_email_info(self, email_data: Dict[str, Any]):
        logger.info("== 收到新邮件 ==")
        logger.info(f"发件人: {self._format_address_list(email_data['from'])}")
        logger.info(f"收件人: {self._format_address_list(email_data['to'])}")
        
        if email_data['cc']:
            logger.info(f"抄送人: {self._format_address_list(email_data['cc'])}")
        
        if email_data['bcc']:
            logger.info(f"密送人: {self._format_address_list(email_data['bcc'])}")
        
        logger.info(f"主题: {email_data['subject'] or '无主题'}")
        logger.info(f"发送时间: {email_data['date']}")
        logger.info(f"Message-ID: {email_data['message_id']}")
        
        if email_data['body']['full']:
            body_preview = email_data['body']['full'][:500] + '...' if len(email_data['body']['full']) > 500 else email_data['body']['full']
            logger.info(f"正文内容: {body_preview}")
        
        if email_data['attachments']:
            logger.info(f"附件数量: {len(email_data['attachments'])}")
            for idx, attachment in enumerate(email_data['attachments'], 1):
                logger.info(f"  {idx}. {attachment['filename']} ({attachment['size']} bytes, {attachment['content_type']})")
        
        logger.info("================")

    def _format_address_list(self, addresses: List[Dict[str, str]]) -> str:
        result = []
        for addr in addresses:
            name = addr.get('name', '')
            address = addr.get('address', '')
            if name:
                result.append(f"{name} <{address}>")
            else:
                result.append(address)
        return ', '.join(result)