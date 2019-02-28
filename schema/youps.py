from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, User
from django.core.mail import send_mail
from django.db import models
from django.utils.http import urlquote
from jsonfield import JSONField
from oauth2client.django_orm import FlowField, CredentialsField

from http_handler import settings
from http_handler.settings import AUTH_USER_MODEL

import ast

class ImapAccount(models.Model):
    # Primary Key
    id = models.AutoField(primary_key=True)

    # TODO we need to remove this
    newest_msg_id = models.IntegerField(default=-1)

    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )

	is_oauth = models.BooleanField(default=False)
	access_token = models.CharField('access_token', max_length=200, blank=True)
	refresh_token = models.CharField('refresh_token', max_length=200, blank=True)
	is_initialized = models.BooleanField(default=False)

    password = models.CharField('password', max_length=100, blank=True)
    host = models.CharField('host', max_length=100)

    is_oauth = models.BooleanField(default=False)
    access_token = models.CharField('access_token', max_length=200, blank=True)
    refresh_token = models.CharField('refresh_token', max_length=200, blank=True)

    current_mode = models.ForeignKey('MailbotMode', null=True, blank=True)
    shortcuts = models.TextField(default="")

    # code = models.TextField(null=True, blank=True)
    # TODO should we store execution logs forever? maybe this should be a foreign key
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

# we save folders flat. e.g., parents/child
class Folder_Model(models.Model):
    id = models.AutoField(primary_key=True)
    uid_next = models.IntegerField(default=-1)
    uid_validity = models.IntegerField(default=-1)
    last_seen_uid = models.IntegerField(default=-1)
    name = models.CharField('name', max_length=300, blank=True)
    imap_account = models.ForeignKey('ImapAccount')

    # to keep track of changes of flags within folder
    highest_modseq = models.IntegerField(default=-1)
    flags = models.TextField(null=True, blank=True)  # a strigified list of flags

    def set_flags(self, flag_lst):
        self.flags = repr(flag_lst)
        
    def get_flags(self):
        return ast.literal_eval( self.flags )

    class Meta:
        db_table = "youps_folder"
        unique_together = ("name", "imap_account")

# This model is to have many-to-many relation of MailbotMode and Folder
class MailbotMode_Folder(models.Model):
    mode = models.ForeignKey('MailbotMode')
    folder = models.ForeignKey('Folder_Model')
    imap_account = models.ForeignKey('ImapAccount')

    class Meta:
        db_table = "youps_mailbotmode_folder"
        unique_together = ("mode", "folder")
    pass

class Message_Thread(models.Model):
    id = models.AutoField(primary_key=True)
    imap_account = models.ForeignKey('ImapAccount')

    progress = models.CharField('progress', max_length=300, blank=True)
    deadline = models.DateTimeField('deadline', null=True, blank=True)
    category = models.CharField('category', max_length=300, blank=True)
    topic = models.CharField('topic', max_length=300, blank=True)
    priority = models.CharField('priority', max_length=300, blank=True)
    task = models.CharField('task', max_length=300, blank=True)

    class Meta:
        db_table = "youps_threads"
        unique_together = ("id", "imap_account")

class Message(models.Model):
    message_id = models.CharField('message_id', max_length=300)

    thread = models.ForeignKey('Message_Thread')
    imap_account = models.ForeignKey('ImapAccount')

    progress = models.CharField('progress', max_length=300, blank=True)
    deadline = models.DateTimeField('deadline', null=True, blank=True)
    category = models.CharField('category', max_length=300, blank=True)
    topic = models.CharField('topic', max_length=300, blank=True)
    priority = models.CharField('priority', max_length=300, blank=True)
    task = models.CharField('task', max_length=300, blank=True)
    
    class Meta:
        db_table = "youps_messages"
        unique_together = ("message_id", "imap_account")

class Contact(models.Model):
    name = models.CharField('contact_name', max_length=100)
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    organization = models.TextField(null=True, blank=True)
    geolocation = models.TextField(null=True, blank=True)
    availability = models.TextField(null=True, blank=True)

    imap_account = models.ForeignKey('ImapAccount') # it belongs to this imap_account

    class Meta:
        unique_together = ("email", "imap_account")

# class Youps_user(models.Model):
