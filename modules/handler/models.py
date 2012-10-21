from django.db import models

'''
Slow_Email Models

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''

class Post(models.Model):
	id = models.AutoField(primary_key=True)
	from_addr = models.CharField(max_length=50)
	message = models.TextField()
	timestamp = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return self.name
	
	class Meta:
		db_table = "posts"


class Active_Members(models.Model):
	id = models.AutoField(primary_key=True)
	message = models.ForeignKey('post')
	active_list = models.TextField()
	timestamp = models.DateTimeField(auto_now=True)
	def __unicode__(self):
		return self.name

	class Meta:
		db_table = "active_members"


