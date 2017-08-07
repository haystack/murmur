import hashlib
import time
import random

from schema.models import Attachment

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def upload_attachments(attachments, msg_id):
    res = ""
    for attachment in attachments:

        filename = attachment['filename']
        attachment_file = attachment['content']
        content_id = attachment['id']

        hash_collision = True
        while hash_collision:
            salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
            thetime = str(time.time())
            hash_filename = hashlib.sha1(filename + salt + thetime).hexdigest()
            hash_collision = Attachment.objects.filter(hash_filename=hash_filename).exists()

        with default_storage.open(hash_filename+'/'+filename, 'wb+') as destination:
            destination.write(attachment_file)

        a = Attachment(msg_id=msg_id, hash_filename=hash_filename, true_filename=filename, content_id=content_id)
        a.save()
    
    return res

def download_attachments(msg_id):

    files = []
    attachments = Attachment.objects.filter(msg_id=msg_id)
    for a in attachments:
        path = a.hash_filename + '/' + a.true_filename 
        with default_storage.open(path, 'r') as f:
            file = {
                'name' : a.true_filename,
                'data' : f.read()
            }
            files.append(file)
    return files