from email import message_from_bytes
from email.header import decode_header
from email.message import Message
from aiosmtpd.smtp import SMTP, Session, Envelope
from utils.attachment import save_attachments


def decode_email_header(header_value):
    if not header_value:
        return ''
    decoded_parts = decode_header(header_value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            if charset:
                try:
                    result.append(part.decode(charset))
                except (UnicodeDecodeError, LookupError):
                    result.append(part.decode('utf-8', errors='replace'))
            else:
                result.append(part.decode('utf-8', errors='replace'))
        else:
            result.append(str(part))
    return ''.join(result)


def is_attachment(part):
    content_disposition = part.get('Content-Disposition', '')
    if 'attachment' in content_disposition.lower():
        return True
    if part.get_filename():
        return True
    return False


def extract_email_body(msg: Message):
    body = []
    if msg.is_multipart():
        for part in msg.walk():
            if is_attachment(part):
                continue
            if part.get_content_type() == 'text/plain':
                charset = part.get_content_charset() or 'utf-8'
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body.append(payload.decode(charset, errors='replace'))
                except Exception as e:
                    print(f"解析正文失败: {e}")
            elif part.get_content_type() == 'text/html':
                charset = part.get_content_charset() or 'utf-8'
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body.append(payload.decode(charset, errors='replace'))
                except Exception as e:
                    print(f"解析HTML正文失败: {e}")
    else:
        charset = msg.get_content_charset() or 'utf-8'
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                body.append(payload.decode(charset, errors='replace'))
        except Exception as e:
            print(f"解析正文失败: {e}")
    return '\n'.join(body)


class CustomMailHandler:
    async def handle_DATA(self, server: SMTP, session: Session, envelope: Envelope):
        print("== 收到新邮件 ==")
        print(f"发件人: {envelope.mail_from}")
        print(f"收件人: {envelope.rcpt_tos}")

        msg = message_from_bytes(envelope.content)

        subject = decode_email_header(msg.get('Subject'))
        print(f"主题: {subject if subject else '无主题'}")

        cc_list = msg.get('Cc', '')
        if cc_list:
            cc_addrs = [addr.strip() for addr in cc_list.split(',')]
            cc_addrs_decoded = [decode_email_header(addr) for addr in cc_addrs]
            print(f"抄送人: {', '.join(cc_addrs_decoded)}")

        body = extract_email_body(msg)
        print("正文内容:")
        print(body)

        await save_attachments(msg)

        print("================\n")

        return '250 Message accepted for delivery'