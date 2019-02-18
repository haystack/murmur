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

<<<<<<< HEAD
from djcelery.models import PeriodicTask, IntervalSchedule
from datetime import datetime

class TaskScheduler(models.Model):

    periodic_task = models.ForeignKey(PeriodicTask)

    @staticmethod
    def schedule_every(task_name, period, every, ptask_name=None, args=None, kwargs=None):
        """ schedules a task by name every "every" "period". So an example call would be:
        TaskScheduler('mycustomtask', 'seconds', 30, [1,2,3]) 
        that would schedule your custom task to run every 30 seconds with the arguments 1,2 and 3 passed to the actual task. """
        permissible_periods = ['days', 'hours', 'minutes', 'seconds']
        if period not in permissible_periods:
            raise Exception('Invalid period specified')
        # create the periodic task and the interval
        if ptask_name is None:
            ptask_name = "%s_%s" % (task_name, datetime.now()) # create some name for the period task
        interval_schedules = IntervalSchedule.objects.filter(period=period, every=every)
        if interval_schedules: # just check if interval schedules exist like that already and reuse em
            interval_schedule = interval_schedules[0]
        else: # create a brand new interval schedule
            interval_schedule = IntervalSchedule()
            interval_schedule.every = every # should check to make sure this is a positive int
            interval_schedule.period = period
            interval_schedule.save()
        ptask = PeriodicTask(name=ptask_name, task=task_name, interval=interval_schedule)
        if args:
            ptask.args = args
        if kwargs:
            ptask.kwargs = kwargs
        ptask.save()
        return TaskScheduler.objects.create(periodic_task=ptask)

    def stop(self):
        """pauses the task"""
        ptask = self.periodic_task
        ptask.enabled = False
        ptask.save()

    def start(self):
        """starts the task"""
        ptask = self.periodic_task
        ptask.enabled = True
        ptask.save()

    def terminate(self):
        self.stop()
        ptask = self.periodic_task
        self.delete()
        ptask.delete()
=======
# class Youps_user(models.Model):
>>>>>>> master
