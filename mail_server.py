import asyncio
from aiosmtpd.controller import Controller
from email import message_from_bytes

class CustomMailHandler:
    async def handle_DATA(self, server, session, envelope):
        print(dir(envelope))  # 打印原始邮件内容（字节流）

        # envelope 包含了发件人、收件人和邮件原始数据
        print("== 收到新邮件 ==")
        print(f"发件人: {envelope.mail_from}")
        print(f"收件人: {envelope.rcpt_tos}")
        
        # 将字节流转换为 email.message.Message 对象以便于读取
        msg = message_from_bytes(envelope.content)
        
        # 打印邮件主题
        print(f"主题: {msg.get('Subject', '无主题')}")
        
        # 提取并打印邮件正文
        print("正文内容:")
        if msg.is_multipart():
            for part in msg.walk():
                # 只提取纯文本部分
                if part.get_content_type() == 'text/plain':
                    print(part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8'))
        else:
            print(msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8'))
            
        print("================\n")
        
        # 返回 250 状态码，告诉发送方邮件已成功接收
        return '250 Message accepted for delivery'

if __name__ == '__main__':
    # 初始化处理器
    handler = CustomMailHandler()
    
    # 设置控制器监听本地的 1025 端口
    # 注意：标准 SMTP 端口是 25，但在 Linux/Mac 上绑定 25 端口需要 root 权限，
    # 所以测试时通常使用 1025 或 8025。
    controller = Controller(handler, hostname='127.0.0.1', port=1025)
    
    # 启动服务器
    controller.start()
    print("SMTP 服务器已启动，正在监听 127.0.0.1:1025 ...")
    print("按 Ctrl+C 停止服务器。")
    
    # 保持主线程运行
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\n服务器正在关闭...")
    finally:
        controller.stop()