import os
from email.message import Message
from config import ATTACHMENTS_DIR


async def save_attachments(msg: Message):
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

    if msg.is_multipart():
        for part in msg.walk():
            content_disposition = part.get('Content-Disposition', None)
            if content_disposition and 'attachment' in content_disposition.lower():
                filename = part.get_filename()
                if filename:
                    if isinstance(filename, bytes):
                        filename = filename.decode('utf-8')
                    else:
                        filename = str(filename)

                    try:
                        filepath = os.path.join(ATTACHMENTS_DIR, filename)
                        with open(filepath, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        print(f"附件已保存: {filepath}")
                    except Exception as e:
                        print(f"保存附件失败 {filename}: {e}")