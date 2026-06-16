from email import message_from_bytes
from aiosmtpd.smtp import SMTP, Session, Envelope
from utils.attachment import save_attachments


class CustomMailHandler:
    async def handle_DATA(self, server: SMTP, session: Session, envelope: Envelope):
        print("== 收到新邮件 ==")
        print(f"发件人: {envelope.mail_from}")
        print(f"收件人: {envelope.rcpt_tos}")

        msg = message_from_bytes(envelope.content)

        print(f"主题: {msg.get('Subject', '无主题')}")

        cc_list = msg.get('Cc', '')
        if cc_list:
            cc_addrs = [addr.strip() for addr in cc_list.split(',')]
            print(f"抄送人: {', '.join(cc_addrs)}")

        print("正文内容:")
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    print(part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8'))
        else:
            print(msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8'))

        await save_attachments(msg)

        print("================\n")

        return '250 Message accepted for delivery'