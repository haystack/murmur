from django.db import models
import json
import typing as t  # noqa: F401 ignore unused we use it for typing
import logging

logger = logging.getLogger('youps')  # type: logging.Logger

class ImapAccount(models.Model):
    
    # the primary key
    id = models.AutoField(primary_key=True)

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

class FolderSchema(models.Model):
    # the primary key
    id = models.AutoField(primary_key=True)
    # each folder is associated with a single ImapAccount
    imap_account = models.ForeignKey(ImapAccount)
    # new messages have a uid >= uid_next if we get a new message this value changes
    # TODO determine better way of specifying not initiated -1 can be used
    uid_next = models.IntegerField(default=-1)
    # if this changes we have to invalidate our entire cache and refresh
    uid_validity = models.IntegerField(default=-1)
    # the name of the folder including it's entire path i.e. "work/project/youps"
    # TODO we need to determine the actual max length CHARFIELD cause mysql indexess`
    name = models.CharField(max_length=300)
    # the last seen uid which is helpful for reducing bandwith when syncing
    last_seen_uid = models.IntegerField(default=-1)
    # the flags associated with the folder 
    _flags = models.TextField(db_column="flags")

    is_selectable =  models.BooleanField(default=False)

    @property
    def flags(self):
        # type: () -> t.List[t.AnyStr]
        return json.loads(self._flags)

    @flags.setter
    def flags(self, value):
        # type: (t.List[t.AnyStr]) -> None
        self._flags = json.dumps(value)

    class Meta:
        db_table = "youps_folder"
        unique_together = ("name", "imap_account")


class MessageSchema(models.Model):
    # the primary key
    id = models.AutoField(primary_key=True)
    # TODO we can possibly get rid of imap_account since imap -> folder -> msg
    # each message is associated with a single ImapAccount
    imap_account = models.ForeignKey('ImapAccount')
    # each message is associated with a single Folder
    folder_schema = models.ForeignKey(FolderSchema)
    # each message has a uid
    uid = models.IntegerField(default=-1)
    # the message sequence number identifies the offest of the message in the folder
    msn = models.IntegerField(default=-1)
    # the flags associated with the message
    _flags = models.TextField(db_column="flags")

    @property
    def flags(self):
        # type: () -> t.List[t.AnyStr]
        return json.loads(self._flags)

    @flags.setter
    def flags(self, value):
        # type: (t.List[t.AnyStr]) -> None
        self._flags = json.dumps(value)


    progress = models.CharField('progress', max_length=300, blank=True)
    deadline = models.DateTimeField('deadline', null=True, blank=True)
    category = models.CharField('category', max_length=300, blank=True)
    topic = models.CharField('topic', max_length=300, blank=True)
    priority = models.CharField('priority', max_length=300, blank=True)
    task = models.CharField('task', max_length=300, blank=True)

    class Meta:
        db_table = "youps_message"
        # message uid is unique per folder, folder is already unique per account
        unique_together = ("uid", "folder_schema")


class MailbotMode(models.Model):
    uid = models.IntegerField()

    name = models.CharField('mode_name', max_length=100)
    code = models.TextField(null=True, blank=True)

    imap_account = models.ForeignKey('ImapAccount')

    class Meta:
        unique_together = ("uid", "imap_account")


# This model is to have many-to-many relation of MailbotMode and Folder
class MailbotMode_Folder(models.Model):
    mode = models.ForeignKey('MailbotMode')
    folder = models.ForeignKey('FolderSchema')
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

    imap_account = models.ForeignKey('ImapAccount')  # it belongs to this imap_account

    class Meta:
        unique_together = ("email", "imap_account")

