import unittest
from unittest.mock import MagicMock
from aiosmtpd.smtp import AuthResult, LoginPassword
from smtp.authenticator import my_authenticator


class TestAuthenticator(unittest.TestCase):
    def setUp(self):
        self.server = MagicMock()
        self.session = MagicMock()
        self.envelope = MagicMock()

    def test_valid_credentials(self):
        auth_data = LoginPassword(login=b'admin@example.com', password=b'secret123')
        result = my_authenticator(self.server, self.session, self.envelope, 'LOGIN', auth_data)
        self.assertTrue(result.success)

    def test_invalid_password(self):
        auth_data = LoginPassword(login=b'admin@example.com', password=b'wrongpass')
        result = my_authenticator(self.server, self.session, self.envelope, 'LOGIN', auth_data)
        self.assertFalse(result.success)

    def test_unknown_user(self):
        auth_data = LoginPassword(login=b'unknown@example.com', password=b'secret123')
        result = my_authenticator(self.server, self.session, self.envelope, 'LOGIN', auth_data)
        self.assertFalse(result.success)

    def test_invalid_mechanism(self):
        auth_data = LoginPassword(login=b'admin@example.com', password=b'secret123')
        result = my_authenticator(self.server, self.session, self.envelope, 'CRAM-MD5', auth_data)
        self.assertFalse(result.success)
        self.assertFalse(result.handled)

    def test_invalid_auth_data(self):
        result = my_authenticator(self.server, self.session, self.envelope, 'LOGIN', 'invalid_data')
        self.assertFalse(result.success)
        self.assertFalse(result.handled)


if __name__ == '__main__':
    unittest.main()