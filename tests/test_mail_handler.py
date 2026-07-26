import unittest
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from handler.mail_handler import decode_email_header, extract_email_body
from utils.attachment import save_attachments
from config import ATTACHMENTS_DIR


class TestMailHandlerUtils(unittest.TestCase):
    def test_decode_email_header_plain(self):
        result = decode_email_header("Test Subject")
        self.assertEqual(result, "Test Subject")

    def test_decode_email_header_none(self):
        result = decode_email_header(None)
        self.assertEqual(result, "")

    def test_decode_email_header_empty(self):
        result = decode_email_header("")
        self.assertEqual(result, "")

    def test_decode_email_header_chinese(self):
        encoded = str(Header("中文主题", 'utf-8'))
        result = decode_email_header(encoded)
        self.assertEqual(result, "中文主题")

    def test_decode_email_header_mixed(self):
        encoded = str(Header("中文 and English", 'utf-8'))
        result = decode_email_header(encoded)
        self.assertIn("中文", result)
        self.assertIn("and English", result)

    def test_extract_email_body_plain(self):
        msg = MIMEText("Hello World", 'plain', 'utf-8')
        body = extract_email_body(msg)
        self.assertEqual(body, "Hello World")

    def test_extract_email_body_with_attachment(self):
        msg = MIMEMultipart()
        msg.attach(MIMEText("Email body", 'plain', 'utf-8'))
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(b'attachment content')
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment', filename='test.txt')
        msg.attach(part)
        
        body = extract_email_body(msg)
        self.assertEqual(body, "Email body")
        self.assertNotIn("attachment content", body)

    def test_extract_email_body_html(self):
        msg = MIMEText("<html><body>Hello</body></html>", 'html', 'utf-8')
        body = extract_email_body(msg)
        self.assertEqual(body, "<html><body>Hello</body></html>")

    def test_extract_email_body_multipart_mixed(self):
        msg = MIMEMultipart('mixed')
        msg.attach(MIMEText("Plain body", 'plain', 'utf-8'))
        msg.attach(MIMEText("<html>HTML body</html>", 'html', 'utf-8'))
        
        body = extract_email_body(msg)
        self.assertIn("Plain body", body)
        self.assertIn("HTML body", body)

    def test_extract_email_body_only_attachment(self):
        msg = MIMEMultipart()
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(b'only attachment')
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment', filename='test.txt')
        msg.attach(part)
        
        body = extract_email_body(msg)
        self.assertEqual(body, "")

    def test_extract_email_body_empty(self):
        msg = MIMEText("", 'plain', 'utf-8')
        body = extract_email_body(msg)
        self.assertEqual(body, "")


class TestAttachmentHandling(unittest.TestCase):
    def setUp(self):
        os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
        for f in os.listdir(ATTACHMENTS_DIR):
            os.remove(os.path.join(ATTACHMENTS_DIR, f))

    def tearDown(self):
        if os.path.exists(ATTACHMENTS_DIR):
            for f in os.listdir(ATTACHMENTS_DIR):
                os.remove(os.path.join(ATTACHMENTS_DIR, f))

    def test_save_attachments_single(self):
        msg = MIMEMultipart()
        msg.attach(MIMEText("Body", 'plain', 'utf-8'))
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(b'test content')
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment', filename='test1.txt')
        msg.attach(part)
        
        import asyncio
        asyncio.run(save_attachments(msg))
        
        self.assertTrue(os.path.exists(os.path.join(ATTACHMENTS_DIR, 'test1.txt')))
        with open(os.path.join(ATTACHMENTS_DIR, 'test1.txt'), 'rb') as f:
            self.assertEqual(f.read(), b'test content')

    def test_save_attachments_multiple(self):
        msg = MIMEMultipart()
        msg.attach(MIMEText("Body", 'plain', 'utf-8'))
        
        for i in range(3):
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f'file {i}'.encode())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=f'file{i}.txt')
            msg.attach(part)
        
        import asyncio
        asyncio.run(save_attachments(msg))
        
        for i in range(3):
            filepath = os.path.join(ATTACHMENTS_DIR, f'file{i}.txt')
            self.assertTrue(os.path.exists(filepath))
            with open(filepath, 'rb') as f:
                self.assertEqual(f.read(), f'file {i}'.encode())

    def test_save_attachments_chinese_filename(self):
        msg = MIMEMultipart()
        msg.attach(MIMEText("Body", 'plain', 'utf-8'))
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(b'chinese content')
        encoders.encode_base64(part)
        filename = Header('中文文件.txt', 'utf-8').encode()
        part.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(part)
        
        import asyncio
        asyncio.run(save_attachments(msg))
        
        filepath = os.path.join(ATTACHMENTS_DIR, '中文文件.txt')
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'rb') as f:
            self.assertEqual(f.read(), b'chinese content')

    def test_save_attachments_none(self):
        msg = MIMEText("Body", 'plain', 'utf-8')
        
        import asyncio
        asyncio.run(save_attachments(msg))
        
        self.assertEqual(len(os.listdir(ATTACHMENTS_DIR)), 0)


if __name__ == '__main__':
    unittest.main()