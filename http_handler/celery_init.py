from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'http_handler.settings')
app = Celery('http_handler')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

@app.task(name="add_task")
def add_task(imap_account, mode):
    """sends an email when feedback form is filled successfully"""
    logger.info("ADD TASK performed!")

    # determine it is periodic or not 
    # callback to user profile to make sure we are not running out-dated code
    print("ADD TASK performed!" + imap_account.email)
    return imap_account.email