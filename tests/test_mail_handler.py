import unittest
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from handler.mail_handler import EmailParser, EmailParseError
from utils.attachment import save_attachments
from config import ATTACHMENTS_DIR


class TestEmailParser(unittest.TestCase):
    def test_parse_simple_email(self):
        msg = MIMEText("Hello World", 'plain', 'utf-8')
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'Test Subject'
        
        parser = EmailParser()
        email_data = parser.parse_from_string(msg.as_string())
        
        self.assertEqual(email_data['from'][0]['address'], 'sender@example.com')
        self.assertEqual(email_data['to'][0]['address'], 'recipient@example.com')
        self.assertEqual(email_data['subject'], 'Test Subject')
        self.assertIn('Hello World', email_data['body']['full'])

    def test_parse_email_with_chinese_subject(self):
        msg = MIMEText("中文正文", 'plain', 'utf-8')
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = Header('中文主题', 'utf-8')
        
        parser = EmailParser()
        email_data = parser.parse_from_string(msg.as_string())
        
        self.assertEqual(email_data['subject'], '中文主题')
        self.assertIn('中文正文', email_data['body']['full'])

    def test_parse_email_with_cc(self):
        msg = MIMEText("Test body", 'plain', 'utf-8')
        msg['From'] = 'sender@example.com'
        msg['To'] = 'to@example.com'
        msg['Cc'] = 'cc1@example.com, cc2@example.com'
        msg['Subject'] = 'Test with CC'
        
        parser = EmailParser()
        email_data = parser.parse_from_string(msg.as_string())
        
        self.assertEqual(len(email_data['cc']), 2)
        cc_addresses = [cc['address'] for cc in email_data['cc']]
        self.assertIn('cc1@example.com', cc_addresses)
        self.assertIn('cc2@example.com', cc_addresses)

    def test_parse_email_with_name(self):
        msg = MIMEText("Test body", 'plain', 'utf-8')
        msg['From'] = 'Sender Name <sender@example.com>'
        msg['To'] = 'Recipient Name <recipient@example.com>'
        msg['Subject'] = 'Test'
        
        parser = EmailParser()
        email_data = parser.parse_from_string(msg.as_string())
        
        self.assertEqual(email_data['from'][0]['name'], 'Sender Name')
        self.assertEqual(email_data['from'][0]['address'], 'sender@example.com')
        self.assertEqual(email_data['to'][0]['name'], 'Recipient Name')
        self.assertEqual(email_data['to'][0]['address'], 'recipient@example.com')

    def test_parse_email_with_html_body(self):
        msg = MIMEMultipart('alternative')
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'HTML Test'
        
        msg.attach(MIMEText("Plain text", 'plain', 'utf-8'))
        msg.attach(MIMEText("<html><body>HTML content</body></html>", 'html', 'utf-8'))
        
        parser = EmailParser()
        email_data = parser.parse_from_string(msg.as_string())
        
        self.assertIn('Plain text', email_data['body']['plain'][0])
        self.assertIn('HTML content', email_data['body']['html'][0])

    def test_parse_email_with_attachment(self):
        msg = MIMEMultipart()
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'Test with attachment'
        
        msg.attach(MIMEText("Email body", 'plain', 'utf-8'))
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(b'attachment content')
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment', filename='test.txt')
        msg.attach(part)
        
        parser = EmailParser()
        email_data = parser.parse_from_string(msg.as_string())
        
        self.assertEqual(len(email_data['attachments']), 1)
        self.assertEqual(email_data['attachments'][0]['filename'], 'test.txt')
        self.assertEqual(email_data['attachments'][0]['binary'], b'attachment content')

    def test_parse_email_with_multiple_attachments(self):
        msg = MIMEMultipart()
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'Test with multiple attachments'
        
        msg.attach(MIMEText("Body", 'plain', 'utf-8'))
        
        for i in range(3):
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f'file {i}'.encode())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=f'file{i}.txt')
            msg.attach(part)
        
        parser = EmailParser()
        email_data = parser.parse_from_string(msg.as_string())
        
        self.assertEqual(len(email_data['attachments']), 3)
        filenames = [att['filename'] for att in email_data['attachments']]
        self.assertIn('file0.txt', filenames)
        self.assertIn('file1.txt', filenames)
        self.assertIn('file2.txt', filenames)

    def test_parse_email_with_chinese_attachment_name(self):
        msg = MIMEMultipart()
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'Test'
        
        msg.attach(MIMEText("Body", 'plain', 'utf-8'))
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(b'chinese content')
        encoders.encode_base64(part)
        filename = Header('中文文件.txt', 'utf-8').encode()
        part.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(part)
        
        parser = EmailParser()
        email_data = parser.parse_from_string(msg.as_string())
        
        self.assertEqual(len(email_data['attachments']), 1)
        self.assertEqual(email_data['attachments'][0]['filename'], '中文文件.txt')

    def test_parse_empty_email(self):
        msg = MIMEText("", 'plain', 'utf-8')
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        
        parser = EmailParser()
        email_data = parser.parse_from_string(msg.as_string())
        
        self.assertEqual(email_data['body']['full'], '')

    def test_parse_invalid_content(self):
        parser = EmailParser()
        
        email_data = parser.parse_from_bytes(b'invalid email content')
        
        self.assertEqual(email_data['from'], [])
        self.assertEqual(email_data['to'], [])
        self.assertEqual(email_data['subject'], '')

    def test_parse_from_bytes(self):
        msg = MIMEText("Hello World", 'plain', 'utf-8')
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'Test Subject'
        
        parser = EmailParser()
        email_data = parser.parse_from_bytes(msg.as_string().encode('utf-8'))
        
        self.assertEqual(email_data['from'][0]['address'], 'sender@example.com')
        self.assertEqual(email_data['to'][0]['address'], 'recipient@example.com')
        self.assertEqual(email_data['subject'], 'Test Subject')


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
        email_data = {
            'attachments': [{
                'filename': 'test1.txt',
                'binary': b'test content'
            }]
        }
        
        import asyncio
        asyncio.run(save_attachments(email_data))
        
        self.assertTrue(os.path.exists(os.path.join(ATTACHMENTS_DIR, 'test1.txt')))
        with open(os.path.join(ATTACHMENTS_DIR, 'test1.txt'), 'rb') as f:
            self.assertEqual(f.read(), b'test content')

    def test_save_attachments_multiple(self):
        email_data = {
            'attachments': [
                {'filename': 'file0.txt', 'binary': b'file 0'},
                {'filename': 'file1.txt', 'binary': b'file 1'},
                {'filename': 'file2.txt', 'binary': b'file 2'}
            ]
        }
        
        import asyncio
        asyncio.run(save_attachments(email_data))
        
        for i in range(3):
            filepath = os.path.join(ATTACHMENTS_DIR, f'file{i}.txt')
            self.assertTrue(os.path.exists(filepath))
            with open(filepath, 'rb') as f:
                self.assertEqual(f.read(), f'file {i}'.encode())

    def test_save_attachments_chinese_filename(self):
        email_data = {
            'attachments': [{
                'filename': '中文文件.txt',
                'binary': b'chinese content'
            }]
        }
        
        import asyncio
        asyncio.run(save_attachments(email_data))
        
        filepath = os.path.join(ATTACHMENTS_DIR, '中文文件.txt')
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'rb') as f:
            self.assertEqual(f.read(), b'chinese content')

    def test_save_attachments_none(self):
        email_data = {
            'attachments': []
        }
        
        import asyncio
        asyncio.run(save_attachments(email_data))
        
        self.assertEqual(len(os.listdir(ATTACHMENTS_DIR)), 0)

    def test_save_attachments_with_empty_binary(self):
        email_data = {
            'attachments': [{
                'filename': 'empty.txt',
                'binary': b''
            }]
        }
        
        import asyncio
        asyncio.run(save_attachments(email_data))
        
        self.assertEqual(len(os.listdir(ATTACHMENTS_DIR)), 0)


if __name__ == '__main__':
    unittest.main()