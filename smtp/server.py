from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP, Session
from .session import ModernSession


class ModernSMTP(SMTP):
    def _create_session(self) -> Session:
        return ModernSession(self.loop)


class ModernController(Controller):
    def factory(self):
        return ModernSMTP(self.handler, **self.SMTP_kwargs)