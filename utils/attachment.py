import os
from typing import Dict, Any, List
from config import ATTACHMENTS_DIR


async def save_attachments(email_data: Dict[str, Any]):
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
    
    attachments: List[Dict[str, Any]] = email_data.get('attachments', [])
    
    for attachment in attachments:
        filename = attachment.get('filename', '')
        if not filename:
            continue
        
        binary_data = attachment.get('binary', b'')
        if not binary_data:
            continue
        
        try:
            filepath = os.path.join(ATTACHMENTS_DIR, filename)
            with open(filepath, 'wb') as f:
                f.write(binary_data)
            print(f"附件已保存: {filepath}")
        except Exception as e:
            print(f"保存附件失败 {filename}: {e}")