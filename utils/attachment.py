import os
from email.message import Message
from email.header import decode_header
from config import ATTACHMENTS_DIR


def decode_filename(filename):
    if not filename:
        return None
    if isinstance(filename, bytes):
        filename = filename.decode('utf-8', errors='replace')
    decoded_parts = decode_header(filename)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            if charset:
                try:
                    result.append(part.decode(charset))
                except (UnicodeDecodeError, LookupError):
                    result.append(part.decode('utf-8', errors='replace'))
            else:
                result.append(part.decode('utf-8', errors='replace'))
        else:
            result.append(str(part))
    return ''.join(result)


async def save_attachments(msg: Message):
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

    if msg.is_multipart():
        for part in msg.walk():
            content_disposition = part.get('Content-Disposition', '')
            is_attachment_flag = False
            
            if 'attachment' in content_disposition.lower():
                is_attachment_flag = True
            elif part.get_filename():
                is_attachment_flag = True
            
            if is_attachment_flag:
                filename = part.get_filename()
                if filename:
                    filename = decode_filename(filename)
                    if not filename:
                        continue

                    try:
                        filepath = os.path.join(ATTACHMENTS_DIR, filename)
                        with open(filepath, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        print(f"附件已保存: {filepath}")
                    except Exception as e:
                        print(f"保存附件失败 {filename}: {e}")