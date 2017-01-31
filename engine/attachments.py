import hashlib
import time
import random

from schema.models import *

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def upload_attachments(attachments, msg_id):
    res = ""
    if attachments:
        for attachment in attachments.get("attachments"):
            salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
            thetime = str(time.time())
            filename = attachment['filename']
            hash_filename = hashlib.sha1(filename + salt + thetime).hexdigest()
            attachment_file = attachment['content']
            with default_storage.open(hash_filename, 'wb+') as destination:
                destination.write(attachment_file)
            a = Attachment(msg_id=msg_id, hash_filename=hash_filename, true_filename=filename)
            a.save()
    return res
    # TODO this only deals with a single attachment; will probably fail for multiple attachments (or just keep the last one?)