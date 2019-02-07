from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, User
from django.core.mail import send_mail
from django.db import models
from django.utils.http import urlquote
from jsonfield import JSONField
from oauth2client.django_orm import FlowField, CredentialsField

from http_handler import settings
from http_handler.settings import AUTH_USER_MODEL

class ImapAccount(models.Model):
	id = models.AutoField(primary_key=True)
	newest_msg_id = models.IntegerField(default=-1)

	email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
	password = models.CharField('password', max_length=100, blank=True)
	host = models.CharField('host', max_length=100)

	is_oauth = models.BooleanField(default=False)
	access_token = models.CharField('access_token', max_length=200, blank=True)
	refresh_token = models.CharField('refresh_token', max_length=200, blank=True)

	current_mode = models.ForeignKey('MailbotMode', null=True, blank=True)
	shortcuts = models.TextField(default="")

	# code = models.TextField(null=True, blank=True)
	execution_log = models.TextField(default="")
	is_test = models.BooleanField(default=True)
	is_running = models.BooleanField(default=False)

	arrive_action = models.CharField('access_token', max_length=1000, blank=True)
	custom_action = models.CharField('custom_action', max_length=1000, blank=True)
	timer_action = models.CharField('timer_action', max_length=1000, blank=True)
	repeat_action = models.CharField('repeat_action', max_length=1000, blank=True)

	# user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)

class MailbotMode(models.Model):
	uid = models.IntegerField()

	name = models.CharField('mode_name', max_length=100)
	code = models.TextField(null=True, blank=True)

	imap_account = models.ForeignKey('ImapAccount')

	class Meta:
		unique_together = ("uid", "imap_account")

class Message(models.Model):
    message_id = models.CharField('message_id', max_length=300)

    thread = models.ForeignKey('Thread')
    imap_account = models.ForeignKey('ImapAccount')

    progress = models.CharField('progress', max_length=300, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    category = models.CharField('category', max_length=300, blank=True)
    topic = models.CharField('topic', max_length=300, blank=True)
    priority = models.CharField('priority', max_length=300, blank=True)
    task = models.CharField('task', max_length=300, blank=True)
    
    class Meta:
		unique_together = ("message_id", "imap_account")

class Thread(models.Model):
    id = models.AutoField(primary_key=True)
    imap_account = models.ForeignKey('ImapAccount')

    progress = models.CharField('progress', max_length=300, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    category = models.CharField('category', max_length=300, blank=True)
    topic = models.CharField('topic', max_length=300, blank=True)
    priority = models.CharField('priority', max_length=300, blank=True)
    task = models.CharField('task', max_length=300, blank=True)

    class Meta:
		unique_together = ("id", "imap_account")
