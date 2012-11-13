from django.db import models

'''
MailX Models

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''

class Post(models.Model):
	id = models.CharField(max_length=50, primary_key=True)
	email = models.CharField(max_length=50)
	subject = models.TextField()
	post = models.TextField()
	reply_to = models.ForeignKey('self', blank=False, null = True, related_name="replies")
	timestamp = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return self.name
	
	class Meta:
		db_table = "posts"

class Group(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=20)
	active = models.BooleanField(default=False)
	timestamp = models.DateTimeField(auto_now=True)
	def __unicode__(self):
		return self.name

	class Meta:
		db_table = "groups"




class User(models.Model):
        id = models.AutoField(primary_key=True)
        email = models.CharField(max_length=50) 
        group = models.ForeignKey('Group')
	admin = models.BooleanField(default=False)
	member = models.BooleanField(default=False)
	moderator = models.BooleanField(default=False)
	guest = models.BooleanField(default=False)
	active = models.BooleanField(default=False)
        def __unicode__(self):
                return self.name

        class Meta:
                db_table = "users"


class Following(models.Model):
	id = models.AutoField(primary_key=True)
	post = models.ForeignKey('Post')
	email = models.CharField(max_length=50)
	timestamp = models.DateTimeField(auto_now=True)
	def __unicode__(self):
		return self.name

	class Meta:
		db_table = "following"


class Like(models.Model):
	id = models.AutoField(primary_key=True)
	post = models.ForeignKey('Post')
	email = models.CharField(max_length=50)
	timestamp = models.DateTimeField(auto_now=True)
	def __unicode__(self):
		return self.name

	class Meta:
		db_table = "likes"



class Dislke(models.Model):
        id = models.AutoField(primary_key=True)
        post = models.ForeignKey('Post')
        email = models.CharField(max_length=50)
        timestamp = models.DateTimeField(auto_now=True)
        def __unicode__(self):
                return self.name

        class Meta:
                db_table = "dislikes"

