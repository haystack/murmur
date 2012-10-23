from django.db import models

'''
Slow_Email Models

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''

class Post(models.Model):
	id = models.CharField(max_length=50, primary_key=True)
	from_email = models.CharField(max_length=50)
	subject = models.TextField()
	message = models.TextField()
	timestamp = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return self.name
	
	class Meta:
		db_table = "posts"

class Group(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=20)
	status = models.BooleanField()
	timestamp = models.DateTimeField(auto_now=True)
	def __unicode__(self):
		return self.name

	class Meta:
		db_table = "groups"




class User(models.Model):
        id = models.AutoField(primary_key=True)
        email = models.CharField(max_length=50) 
        group = models.ForeignKey('Group')
	admin = models.BooleanField()
	status = models.BooleanField()
        def __unicode__(self):
                return self.name

        class Meta:
                db_table = "users"


class Active_Members(models.Model):
	id = models.AutoField(primary_key=True)
	message = models.ForeignKey('Post')
	active_list = models.TextField()
	timestamp = models.DateTimeField(auto_now=True)
	def __unicode__(self):
		return self.name

	class Meta:
		db_table = "active_members"



class Reply(models.Model):
        id = models.AutoField(primary_key=True)
	from_email = models.CharField(max_length=50)
        message = models.ForeignKey('Post')
        reply = models.TextField()
        timestamp = models.DateTimeField(auto_now=True)
        def __unicode__(self):
                return self.name

        class Meta:
                db_table = "replies"
