import time
from smtp.server import ModernController
from handler.mail_handler import CustomMailHandler
from smtp.authenticator import my_authenticator
from config import HOSTNAME, PORT, AUTH_REQUIRE_TLS, AUTH_REQUIRED


def main():
    handler = CustomMailHandler()

    controller = ModernController(
        handler,
        hostname=HOSTNAME,
        port=PORT,
        authenticator=my_authenticator,
        auth_require_tls=AUTH_REQUIRE_TLS,
        auth_required=AUTH_REQUIRED
    )

    controller.start()
    print(f"SMTP 服务器已启动，正在监听 {HOSTNAME}:{PORT} ...")
    print("按 Ctrl+C 停止服务器。")

    try:
        while True:
            time.sleep(0.02)
    except KeyboardInterrupt:
        print("\n检测到 Ctrl+C，服务器正在关闭...")
    finally:
        controller.stop()


if __name__ == '__main__':
    main()