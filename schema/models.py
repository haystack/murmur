from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser

from django.utils.http import urlquote
from django.core.mail import send_mail
from http_handler import settings

class Post(models.Model):
	id = models.AutoField(primary_key=True)
	author = models.ForeignKey(settings.AUTH_USER_MODEL)
	subject = models.TextField()
	msg_id = models.CharField(max_length=120, unique=True)
	post = models.TextField()
	group = models.ForeignKey('Group')
	thread = models.ForeignKey('Thread')
	reply_to = models.ForeignKey('self', blank=False, null = True, related_name="replies")
	timestamp = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return '%s %s' % (self.author.email, self.subject)
	
	class Meta:
		db_table = "mailx_posts"
		ordering = ["timestamp"]


class Thread(models.Model):
	id = models.AutoField(primary_key=True)
	subject = models.TextField()
	timestamp = models.DateTimeField(auto_now=True)
	group = models.ForeignKey('Group')

	def __unicode__(self):
		return '%s in %s' % (self.id, self.group)
	
	class Meta:
		db_table = "mailx_threads"
		ordering = ["-timestamp"]


class TagThread(models.Model):
	thread = models.ForeignKey('Thread')
	tag = models.ForeignKey('Tag')
		
	def __unicode__(self):
		return '%s tag for Thread %s' % (self.tag.name, self.thread.id)
	
	class Meta:
		unique_together = ("thread", "tag")
		
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
	
	def __unicode__(self):
		return '%s - %s' % (self.member.email, self.group.name)

	class Meta:
		db_table = "mailx_membergroups"
		unique_together = ("member", "group")
	

class Group(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=20, unique=True)
	description = models.CharField(max_length=140)
	public = models.BooleanField(default=True)
	active = models.BooleanField(default=True)
	
	allow_attachments = models.BooleanField(default=True)
	
	timestamp = models.DateTimeField(auto_now=True)
	
	def __unicode__(self):
		return self.name

	class Meta:
		db_table = "mailx_groups"



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


class Following(models.Model):
	id = models.AutoField(primary_key=True)
	thread = models.ForeignKey('Thread')
	user = models.ForeignKey(settings.AUTH_USER_MODEL)
	timestamp = models.DateTimeField(auto_now=True)
	
	def __unicode__(self):
		return '%s follows Thread: %s' % (self.user.email, self.thread.id)

	class Meta:
		db_table = "mailx_following"


class Mute(models.Model):
	id = models.AutoField(primary_key=True)
	thread = models.ForeignKey('Thread')
	user = models.ForeignKey(settings.AUTH_USER_MODEL)
	timestamp = models.DateTimeField(auto_now=True)
	
	def __unicode__(self):
		return '%s mutes Thread: %s' % (self.user.email, self.thread.id)

	class Meta:
		db_table = "mailx_mute"

class Upvote(models.Model):
	id = models.AutoField(primary_key=True)
	post = models.ForeignKey('Post')
	user = models.ForeignKey(settings.AUTH_USER_MODEL)
	timestamp = models.DateTimeField(auto_now=True)
	
	def __unicode__(self):
		return '%s likes Post %s' % (self.user.email, self.post.id)

	class Meta:
		db_table = "mailx_likes"


