from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, User
from django.core.mail import send_mail
from django.db import models
from django.utils.http import urlquote
from jsonfield import JSONField
from oauth2client.django_orm import FlowField, CredentialsField

from http_handler import settings
from http_handler.settings import AUTH_USER_MODEL

class Post(models.Model):
	id = models.AutoField(primary_key=True)
	author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_authored_posts', null=True)
	subject = models.TextField()
	msg_id = models.CharField(max_length=120, unique=True)
	post = models.TextField()
	group = models.ForeignKey('Group')
	thread = models.ForeignKey('Thread')
	reply_to = models.ForeignKey('self', blank=False, null=True, related_name="replies")
	timestamp = models.DateTimeField(auto_now=True)
	forwarding_list = models.ForeignKey('ForwardingList', null=True)
	verified_sender = models.BooleanField(default=False)
	# a post's author is the Murmur user (if any) who wrote the post.
	# a post's poster_email is the email address of the user who originally
	# wrote the post. so if author is not null, author.email = poster_email.
	# if the author is null, then the person who wrote the message isn't actually
	# a member of this group on Murmur, and it was likely received via a list that
	# fwds to this Murmur group
	poster_email = models.EmailField(max_length=255, null=True)

	# often "from" header is Firstname LastName <person@website.com>. if so, save that name.
	poster_name = models.CharField(max_length=50, null=True)

	# moderation-related data 

	# what state a message is currently in 
	STATUS_CHOICES = (('R', 'rejected'), ('P', 'pending'), ('A', 'approved'))
	status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')

	# optional explanation from mod about decision
	mod_explanation = models.TextField(null=True)

	# who the moderator that approved or rejected this message was
	who_moderated = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_moderated_posts', null=True)

	perspective_data = JSONField(null=True)

	def __unicode__(self):
		if self.author:
			return '%s %s' % (self.author.email, self.subject)
		return '%s %s' % (self.poster_email, self.subject)
	
	class Meta:
		db_table = "murmur_posts"
		ordering = ["timestamp"]

class Attachment(models.Model):
	id = models.AutoField(primary_key=True)
	msg_id = models.CharField(max_length=120)
	hash_filename = models.TextField(max_length=40)
	true_filename = models.TextField()
	content_id = models.CharField(max_length=120, null=True)
	timestamp = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = "murmur_attachments"
		ordering = ["timestamp"]

class Thread(models.Model):
	id = models.AutoField(primary_key=True)
	subject = models.TextField()
	timestamp = models.DateTimeField(auto_now=True)
	group = models.ForeignKey('Group')

	def __unicode__(self):
		return '%s in %s' % (self.id, self.group)
	
	class Meta:
		db_table = "murmur_threads"
		ordering = ["-timestamp"]

class DoNotSendList(models.Model):
	id = models.AutoField(primary_key=True)
	group = models.ForeignKey('Group')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, unique=False, related_name='donotsend_author')
	donotsend_user = models.ForeignKey(settings.AUTH_USER_MODEL, unique=False, related_name='donotsend_user')
		
	def __unicode__(self):
		return '%s dissimulate user for user %s at group %s' % (self.user.name, self.donotsend_user.name, self.group)

	class Meta:
		db_table = "murmur_donotsend"
		# unique_together = ("user", "group", "donotsend_user")

class TagThread(models.Model):
	thread = models.ForeignKey('Thread')
	tag = models.ForeignKey('Tag')
		
	def __unicode__(self):
		return '%s tag for Thread %s' % (self.tag.name, self.thread.id)
	
	class Meta:
		unique_together = ("thread", "tag")

'''
this is for deciding whether a non-first post in a thread, from 
someone who already posted in the thread, should go through 
moderation. 
'''
class ThreadHash(models.Model):
	group = models.ForeignKey('Group')

	# we store a hash so that we don't keep information about
	# this thread once all its posts are approved.
	sender_subject_hash = models.CharField(max_length=40)

	# if this is True, the group's admin has opted in to keep
	# moderation on for the user's posts to this thread. if it's 
	# False (but this object exists), this user previously posted 
	# and the post was approved. 
	moderate = models.BooleanField(default=False)
		
class Tag(models.Model):
	id = models.AutoField(primary_key=True)
	group = models.ForeignKey('Group')
	color = models.CharField(max_length=6)
	name = models.CharField(max_length=20)
	
	def __unicode__(self):
		return '%s tag for %s' % (self.name, self.group.name)
	
	class Meta:
		unique_together = ("name", "group")
		
class FollowTag(models.Model):
	id = models.AutoField(primary_key=True)
	user = models.ForeignKey(settings.AUTH_USER_MODEL)
	group = models.ForeignKey('Group')
	tag = models.ForeignKey('Tag')
	timestamp = models.DateTimeField(auto_now=True)
	
	def __unicode__(self):
		return '%s follows tag %s' % (self.user.email, self.tag.name)
	
	class Meta:
		unique_together = ("user", "tag")

class MuteTag(models.Model):
	id = models.AutoField(primary_key=True)
	user = models.ForeignKey(settings.AUTH_USER_MODEL)
	group = models.ForeignKey('Group')
	tag = models.ForeignKey('Tag')
	timestamp = models.DateTimeField(auto_now=True)
	
	def __unicode__(self):
		return '%s mutes tag %s' % (self.user.email, self.tag.name)
	
	class Meta:
		unique_together = ("user", "tag")


class MemberGroup(models.Model):
	id = models.AutoField(primary_key=True)
	member = models.ForeignKey(settings.AUTH_USER_MODEL)
	group = models.ForeignKey('Group')
	timestamp = models.DateTimeField(auto_now=True)
	admin = models.BooleanField(default=False)
	moderator = models.BooleanField(default=False)
	no_emails = models.BooleanField(default=False)
	always_follow_thread = models.BooleanField(default=True)
	upvote_emails = models.BooleanField(default=True)
	receive_attachments = models.BooleanField(default=True)
	last_emailed = models.DateTimeField(null=True)
	gmail_filter_hash = models.CharField(max_length=40, null=True)
	last_updated_hash = models.DateTimeField(auto_now_add=True)
	digest = models.BooleanField(default=False)
	
	def __unicode__(self):
		return '%s - %s' % (self.member.email, self.group.name)

	class Meta:
		db_table = "murmur_membergroups"
		unique_together = ("member", "group")

class MemberGroupPending(models.Model):
	id = models.AutoField(primary_key=True)
	member = models.ForeignKey(settings.AUTH_USER_MODEL)
	group = models.ForeignKey('Group')
	timestamp = models.DateTimeField(auto_now=True)
	hash = models.CharField(max_length=40)
	
	def __unicode__(self):
		return '%s - %s' % (self.member.email, self.group.name)

	class Meta:
		db_table = "murmur_membergroupspending"
		unique_together = ("member", "group")

class ForwardingList(models.Model):
	id = models.AutoField(primary_key=True)
	email = models.EmailField(verbose_name='email address',max_length=255)
	timestamp = models.DateTimeField(auto_now=True)
	group = models.ForeignKey('Group')
	url = models.URLField(null=True, blank=True)
	can_post = models.BooleanField(default=False)
	can_receive = models.BooleanField(default=False)

	def __unicode__(self):
		return self.email

class Group(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=20, unique=True)
	description = models.CharField(max_length=140)
	public = models.BooleanField(default=True)
	active = models.BooleanField(default=True)
	allow_attachments = models.BooleanField(default=True)
	timestamp = models.DateTimeField(auto_now=True)
	show_rejected_site = models.BooleanField(default=True)
	send_rejected_tagged = models.BooleanField(default=True)
	# whether moderators can edit whitelist and blacklist 
	mod_edit_wl_bl = models.BooleanField(default=True) 
	# description of policy/rules for moderation
	mod_rules = models.TextField(null=True)

 	# whether to automatically approve emails from a sender to a thread 
 	# in this group after their first post to the thread is approved
 	auto_approve_after_first = models.BooleanField(default=True)
	
	def __unicode__(self):
		return self.name

	class Meta:
		db_table = "murmur_groups"

class WhiteOrBlacklist(models.Model):
	id = models.AutoField(primary_key=True)
	group = models.ForeignKey('Group')
	email = models.EmailField(max_length=255)

	# only one of the following can be true
	whitelist = models.BooleanField(default=False)
	blacklist = models.BooleanField(default=False)

	# timestamp (for temporary bans)
	timestamp = models.DateTimeField(auto_now=True)


class MyUserManager(BaseUserManager):
	def create_user(self, email, password=None):
		"""
        Creates and saves a User with the given email and password.
        """
		if not email:
			raise ValueError('Users must have an email address')

		user = self.model(email=self.normalize_email(email))

		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, password):
		"""
        Creates and saves a superuser with the given email and password.
        """
		user = self.create_user(email,
            password=password
        )
		user.is_admin = True
		user.save(using=self._db)
		return user


class UserProfile(AbstractBaseUser):
	email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
	first_name = models.CharField('first name', max_length=30, blank=True)
	last_name = models.CharField('last name', max_length=30, blank=True)
	is_active = models.BooleanField(default=True)
	is_admin = models.BooleanField(default=False)
	date_joined = models.DateTimeField(auto_now=True)
	hash = models.CharField(max_length=40, default="")
	imapAccount = models.ForeignKey('ImapAccount', blank=True, null=True)

	objects = MyUserManager()

	USERNAME_FIELD = 'email'

	def get_full_name(self):
		"""
        Returns the first_name plus the last_name, with a space in between.
        """
		full_name = '%s %s' % (self.first_name, self.last_name)
		return full_name.strip()

	def get_short_name(self):
		"Returns the short name for the user."
		return self.first_name

	def email_user(self, subject, message, from_email=None):
		"""
        Sends an email to this User.
        """	
		send_mail(subject, message, from_email, [self.email])

	def has_perm(self, perm, obj=None):
		"Does the user have a specific permission?"
		return True

	def has_module_perms(self, app_label):
		"Does the user have permissions to view the app `app_label`?"
		return True

	@property
	def is_staff(self):
		"Is the user a member of staff?"
		return self.is_admin

class ImapAccount(models.Model):
	newest_msg_id = models.IntegerField(default=-1)

	email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
	password = models.CharField('password', max_length=100, blank=True)
	host = models.CharField('host', max_length=100)

	is_oauth = models.BooleanField(default=False)
	access_token = models.CharField('access_token', max_length=100, blank=True)
	refresh_token = models.CharField('refresh_token', max_length=100, blank=True)
	
	arrive_action = models.CharField('access_token', max_length=1000, blank=True)
	custom_action = models.CharField('custom_action', max_length=1000, blank=True)
	timer_action = models.CharField('timer_action', max_length=1000, blank=True)
	repeat_action = models.CharField('repeat_action', max_length=1000, blank=True)

class Following(models.Model):
	id = models.AutoField(primary_key=True)
	thread = models.ForeignKey('Thread')
	user = models.ForeignKey(settings.AUTH_USER_MODEL)
	timestamp = models.DateTimeField(auto_now=True)
	
	def __unicode__(self):
		return '%s follows Thread: %s' % (self.user.email, self.thread.id)

	class Meta:
		db_table = "murmur_following"


class Mute(models.Model):
	id = models.AutoField(primary_key=True)
	thread = models.ForeignKey('Thread')
	user = models.ForeignKey(settings.AUTH_USER_MODEL)
	timestamp = models.DateTimeField(auto_now=True)
	dissimulated = models.BooleanField(default=False)
	
	def __unicode__(self):
		return '%s mutes Thread: %s' % (self.user.email, self.thread.id)

	class Meta:
		db_table = "murmur_mute"

class Upvote(models.Model):
	id = models.AutoField(primary_key=True)
	post = models.ForeignKey('Post')
	user = models.ForeignKey(settings.AUTH_USER_MODEL)
	timestamp = models.DateTimeField(auto_now=True)
	
	def __unicode__(self):
		return '%s likes Post %s' % (self.user.email, self.post.id)

	class Meta:
		db_table = "murmur_likes"

class FlowModel(models.Model):
    id = models.ForeignKey(AUTH_USER_MODEL, primary_key=True)
    flow = FlowField()
 
 
class CredentialsModel(models.Model):
    id = models.ForeignKey(AUTH_USER_MODEL, primary_key=True)
    credential = CredentialsField()

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^schema\.fields\.FlowModel"])
add_introspection_rules([], ["^schema\.fields\.CredentialsModel"])
add_introspection_rules([], ["^oauth2client\.django_orm\.CredentialsField"])
add_introspection_rules([], ["^oauth2client\.django_orm\.FlowField"])