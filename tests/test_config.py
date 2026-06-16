import unittest
from config import HOSTNAME, PORT, AUTH_REQUIRE_TLS, AUTH_REQUIRED, ATTACHMENTS_DIR, VALID_CREDENTIALS


class TestConfig(unittest.TestCase):
    def test_server_config(self):
        self.assertEqual(HOSTNAME, '127.0.0.1')
        self.assertEqual(PORT, 1025)

    def test_auth_config(self):
        self.assertFalse(AUTH_REQUIRE_TLS)
        self.assertTrue(AUTH_REQUIRED)

    def test_attachments_dir(self):
        self.assertEqual(ATTACHMENTS_DIR, 'attachments')

    def test_valid_credentials(self):
        self.assertIn(b'admin@example.com', VALID_CREDENTIALS)
        self.assertEqual(VALID_CREDENTIALS[b'admin@example.com'], b'secret123')


if __name__ == '__main__':
    unittest.main()