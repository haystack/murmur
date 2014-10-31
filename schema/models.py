from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
'''
MailX Models

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''
from django.utils.http import urlquote
from django.core.mail import send_mail
from http_handler import settings

class Post(models.Model):
	id = models.AutoField(primary_key=True)
	author = models.ForeignKey(settings.AUTH_USER_MODEL)
	subject = models.TextField()
	msg_id = models.CharField(max_length=90, unique=True)
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
	subject = models.TextField(unique=True)
	timestamp = models.DateTimeField(auto_now=True)
	group = models.ForeignKey('Group')

	def __unicode__(self):
		return '%s in %s' % (self.id, self.group)
	
	class Meta:
		db_table = "mailx_threads"
		ordering = ["-timestamp"]


class Group(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=20, unique=True)
	public = models.BooleanField(default=True)
	active = models.BooleanField(default=True)
	timestamp = models.DateTimeField(auto_now=True)
	admins = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="admin")
	moderators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="moderator")
	members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="member")
	
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


class Like(models.Model):
	id = models.AutoField(primary_key=True)
	post = models.ForeignKey('Post')
	email = models.CharField(max_length=50)
	timestamp = models.DateTimeField(auto_now=True)
	def __unicode__(self):
		return self.name

	class Meta:
		db_table = "mailx_likes"



class Dislke(models.Model):
	id = models.AutoField(primary_key=True)
	post = models.ForeignKey('Post')
	email = models.CharField(max_length=50)
	timestamp = models.DateTimeField(auto_now=True)
	def __unicode__(self):
		return self.name

	class Meta:
		db_table = "mailx_dislikes"

