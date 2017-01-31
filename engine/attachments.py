import hashlib
import time
import random

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def upload_attachments(attachments):
    print "ABOUT TO UPLOAD FILE"
    attachment_names = ""
    attachment_ids = ""
    for attachment in attachments.get("attachments"):
        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        thetime = str(time.time())
        filename = attachment['filename']
        hash_filename = hashlib.sha1(filename + salt + thetime).hexdigest()
        attachment_file = attachment['content']
        with default_storage.open(hash_filename, 'wb+') as destination:
				for chunk in attachment_file.chunks():
					destination.write(chunk)
        attachment_names = filename
        attachment_ids = hash_filename
        print "FILENAME OF UPLOADED FILE:", hash_filename
    return (attachment_names, attachment_ids)