import hashlib
import time
import random

from schema.models import Attachment

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def upload_attachments(attachments, msg_id):
    res = ""
    if attachments:
        for attachment in attachments.get("attachments"):
            hash_collision = True
            while hash_collision:
                salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
                thetime = str(time.time())
                filename = attachment['filename']
                hash_filename = hashlib.sha1(filename + salt + thetime).hexdigest()
                hash_collision = Attachment.objects.filter(hash_filename=hash_filename).exists()
            attachment_file = attachment['content']
            with default_storage.open(hash_filename+'/'+filename, 'wb+') as destination:
                destination.write(attachment_file)
            a = Attachment(msg_id=msg_id, hash_filename=hash_filename, true_filename=filename)
            a.save()
    return res

def download_attachments(msg_id):

    files = []
    attachments = Attachment.objects.filter(msg_id=msg_id)
    for a in attachments:
        path = a.hash_filename + '/' + a.true_filename 
        with default_storage.open(path, 'r') as f:
            file = {
                'name' : true_filename,
                'data' : f.read()
            }
            files.append(file)
    return files