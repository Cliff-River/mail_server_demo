from aiosmtpd.smtp import Session


class ModernSession(Session):
    @property
    def login_data(self):
        return self._login_data

    @login_data.setter
    def login_data(self, value):
        self._login_data = value