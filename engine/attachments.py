import hashlib
import time
import random

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def upload_attachments(attachments):
    attachment_names = ""
    attachment_ids = ""
    if attachments:
        for attachment in attachments.get("attachments"):
            salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
            thetime = str(time.time())
            filename = attachment['filename']
            hash_filename = hashlib.sha1(filename + salt + thetime).hexdigest()
            attachment_file = attachment['content']
            with default_storage.open(hash_filename, 'wb+') as destination:
                destination.write(attachment_file)
            attachment_names = filename
            attachment_ids = hash_filename
    return (attachment_names, attachment_ids)