import unittest
from smtp.session import ModernSession


class TestModernSession(unittest.TestCase):
    def test_login_data_property(self):
        session = ModernSession(loop=None)
        test_data = {'user': 'test'}
        session.login_data = test_data
        self.assertEqual(session.login_data, test_data)


if __name__ == '__main__':
    unittest.main()