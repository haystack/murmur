from django.db import models
from django.contrib.auth.models import User

'''
MailX Models

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''

class Post(models.Model):
	id = models.AutoField(primary_key=True)
	msg_id = models.CharField(max_length=50, unique=True)
	email = models.CharField(max_length=50)
	subject = models.TextField()
	post = models.TextField()
	group = models.ForeignKey('Group')
	thread = models.ForeignKey('Thread')
	reply_to = models.ForeignKey('self', blank=False, null = True, related_name="replies")
	timestamp = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return self.name
	
	class Meta:
		db_table = "mailx_posts"
		ordering = ["timestamp"]


class Thread(models.Model):
	id = models.AutoField(primary_key=True)
	timestamp = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return self.name
	
	class Meta:
		db_table = "mailx_threads"
		ordering = ["-timestamp"]


class Group(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=20, unique=True)
	public = models.BooleanField(default=True)
	active = models.BooleanField(default=True)
	timestamp = models.DateTimeField(auto_now=True)
	def __unicode__(self):
		return self.name

	class Meta:
		db_table = "mailx_groups"


class UserProfile(models.Model):
	user = models.OneToOneField(User)
# 	
# 	def __unicode__(self):
# 		return self.user.email

	class Meta:
		db_table = "mailx_users"


class Following(models.Model):
	id = models.AutoField(primary_key=True)
	thread = models.ForeignKey('Thread')
	email = models.CharField(max_length=50)
	timestamp = models.DateTimeField(auto_now=True)
	def __unicode__(self):
		return self.name

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

