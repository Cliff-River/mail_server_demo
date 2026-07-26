import unittest
import threading
import time
import os
from unittest.mock import patch, MagicMock
from client import MailClient, MailError, AuthenticationError, SMTPError, send_email_simple, get_default_credentials
from smtp.server import ModernController
from handler.mail_handler import CustomMailHandler
from smtp.authenticator import my_authenticator
from config import HOSTNAME, PORT, AUTH_REQUIRE_TLS, AUTH_REQUIRED


class TestMailClient(unittest.TestCase):
    def setUp(self):
        self.mock_smtp = MagicMock()
        self.mock_smtp.send.return_value = {}

    @patch('client.yagmail.SMTP')
    def test_connect_success(self, mock_yagmail):
        mock_yagmail.return_value = self.mock_smtp
        client = MailClient(
            smtp_host='127.0.0.1',
            smtp_port=1025,
            username='admin@example.com',
            password='secret123',
        )
        client.connect()
        self.assertIsNotNone(client._client)
        mock_yagmail.assert_called_once_with(
            user='admin@example.com',
            password='secret123',
            host='127.0.0.1',
            port=1025,
            smtp_starttls=False,
            smtp_ssl=False,
        )

    @patch('client.yagmail.SMTP')
    def test_connect_failure(self, mock_yagmail):
        mock_yagmail.side_effect = Exception('连接失败')
        client = MailClient()
        with self.assertRaises(ConnectionError):
            client.connect()

    @patch('client.yagmail.SMTP')
    def test_disconnect(self, mock_yagmail):
        mock_yagmail.return_value = self.mock_smtp
        client = MailClient()
        client.connect()
        client.disconnect()
        self.assertIsNone(client._client)
        self.mock_smtp.close.assert_called_once()

    @patch('client.yagmail.SMTP')
    def test_send_email_success(self, mock_yagmail):
        mock_yagmail.return_value = self.mock_smtp
        with MailClient(username='admin@example.com', password='secret123') as client:
            result = client.send_email(
                to=['receiver@example.com'],
                subject='Test Subject',
                contents='Test content',
                cc=['cc@example.com'],
                bcc=['bcc@example.com'],
                attachments=['example.txt'],
            )
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], '邮件发送成功')
        self.mock_smtp.send.assert_called_once()

    @patch('client.yagmail.SMTP')
    def test_send_email_no_connection(self, mock_yagmail):
        client = MailClient()
        with self.assertRaises(RuntimeError) as context:
            client.send_email(
                to=['receiver@example.com'],
                subject='Test',
                contents='Test',
            )
        self.assertIn('请先调用 connect()', str(context.exception))

    @patch('client.yagmail.SMTP')
    def test_send_email_empty_recipients(self, mock_yagmail):
        mock_yagmail.return_value = self.mock_smtp
        with MailClient() as client:
            with self.assertRaises(ValueError) as context:
                client.send_email(
                    to=[],
                    subject='Test',
                    contents='Test',
                )
        self.assertIn('收件人列表不能为空', str(context.exception))

    @patch('client.yagmail.SMTP')
    def test_send_email_empty_subject(self, mock_yagmail):
        mock_yagmail.return_value = self.mock_smtp
        with MailClient() as client:
            with self.assertRaises(ValueError) as context:
                client.send_email(
                    to=['receiver@example.com'],
                    subject='',
                    contents='Test',
                )
        self.assertIn('邮件主题不能为空', str(context.exception))

    @patch('client.yagmail.SMTP')
    def test_send_email_missing_attachment(self, mock_yagmail):
        mock_yagmail.return_value = self.mock_smtp
        with MailClient() as client:
            with self.assertRaises(FileNotFoundError) as context:
                client.send_email(
                    to=['receiver@example.com'],
                    subject='Test',
                    contents='Test',
                    attachments=['nonexistent_file.txt'],
                )
        self.assertIn('附件文件不存在', str(context.exception))

    @patch('client.yagmail.SMTP')
    def test_send_email_authentication_error(self, mock_yagmail):
        import smtplib
        self.mock_smtp.send.side_effect = smtplib.SMTPAuthenticationError(535, b'Auth failed')
        mock_yagmail.return_value = self.mock_smtp
        with MailClient() as client:
            with self.assertRaises(AuthenticationError):
                client.send_email(
                    to=['receiver@example.com'],
                    subject='Test',
                    contents='Test',
                )

    @patch('client.yagmail.SMTP')
    def test_send_email_smtp_error(self, mock_yagmail):
        import smtplib
        self.mock_smtp.send.side_effect = smtplib.SMTPException('SMTP error')
        mock_yagmail.return_value = self.mock_smtp
        with MailClient() as client:
            with self.assertRaises(SMTPError):
                client.send_email(
                    to=['receiver@example.com'],
                    subject='Test',
                    contents='Test',
                )

    @patch('client.yagmail.SMTP')
    def test_send_email_general_error(self, mock_yagmail):
        self.mock_smtp.send.side_effect = Exception('General error')
        mock_yagmail.return_value = self.mock_smtp
        with MailClient() as client:
            with self.assertRaises(MailError):
                client.send_email(
                    to=['receiver@example.com'],
                    subject='Test',
                    contents='Test',
                )

    @patch('client.yagmail.SMTP')
    def test_context_manager(self, mock_yagmail):
        mock_yagmail.return_value = self.mock_smtp
        with MailClient() as client:
            self.assertIsNotNone(client._client)
        self.assertIsNone(client._client)
        self.mock_smtp.close.assert_called_once()


class TestHelperFunctions(unittest.TestCase):
    def test_get_default_credentials(self):
        credentials = get_default_credentials()
        self.assertIsInstance(credentials, dict)
        self.assertIn('admin@example.com', credentials)
        self.assertEqual(credentials['admin@example.com'], 'secret123')

    @patch('client.MailClient')
    def test_send_email_simple(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.send_email.return_value = {'success': True, 'message': '邮件发送成功'}

        result = send_email_simple(
            to=['receiver@example.com'],
            subject='Test',
            contents='Test',
        )

        self.assertTrue(result['success'])
        mock_client.send_email.assert_called_once()

    @patch('client.MailClient')
    def test_send_email_simple_with_custom_credentials(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.send_email.return_value = {'success': True}

        send_email_simple(
            to=['receiver@example.com'],
            subject='Test',
            contents='Test',
            username='custom@example.com',
            password='custompass',
        )

        mock_client_class.assert_called_once_with(
            smtp_host='127.0.0.1',
            smtp_port=1025,
            username='custom@example.com',
            password='custompass',
            use_tls=False,
            use_ssl=False,
        )


class TestMailClientIntegration(unittest.TestCase):
    TEST_HOST = '127.0.0.1'
    TEST_PORT = 1026

    @classmethod
    def setUpClass(cls):
        cls.handler = CustomMailHandler()
        cls.controller = ModernController(
            cls.handler,
            hostname=cls.TEST_HOST,
            port=cls.TEST_PORT,
            authenticator=my_authenticator,
            auth_require_tls=AUTH_REQUIRE_TLS,
            auth_required=AUTH_REQUIRED
        )
        cls.server_thread = threading.Thread(target=cls.controller.start, daemon=True)
        cls.server_thread.start()
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.controller.stop()
        cls.server_thread.join(timeout=2)

    def test_send_email_to_local_server(self):
        with MailClient(
            smtp_host=self.TEST_HOST,
            smtp_port=self.TEST_PORT,
            username='admin@example.com',
            password='secret123',
        ) as client:
            result = client.send_email(
                to=["test@example.com"],
                subject="Integration Test Subject",
                contents="This is an integration test email.",
            )
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], '邮件发送成功')

    def test_send_email_with_cc(self):
        with MailClient(
            smtp_host=self.TEST_HOST,
            smtp_port=self.TEST_PORT,
            username='admin@example.com',
            password='secret123',
        ) as client:
            result = client.send_email(
                to=["test@example.com"],
                subject="Integration Test with CC",
                contents="Email with CC recipients.",
                cc=["cc@example.com", "cc2@example.com"],
            )
        self.assertTrue(result['success'])

    def test_send_email_with_attachment(self):
        test_file = "test_attachment.txt"
        with open(test_file, 'w') as f:
            f.write("Test attachment content")
        
        try:
            with MailClient(
                smtp_host=self.TEST_HOST,
                smtp_port=self.TEST_PORT,
                username='admin@example.com',
                password='secret123',
            ) as client:
                result = client.send_email(
                    to=["test@example.com"],
                    subject="Integration Test with Attachment",
                    contents="Email with attachment.",
                    attachments=[test_file],
                )
            self.assertTrue(result['success'])
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)


if __name__ == '__main__':
    unittest.main()