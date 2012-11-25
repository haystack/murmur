import logging, time, base64, email
from schema.models import *
from msg_codes import *

'''
MailX Controller

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''

def get_all_groups():
	res = {'status':False}
	try:
		groups = Group.objects.all()
		res['status'] = True
		res['groups'] = []
		for g in groups:
			res['groups'].append({'name':g.name, 'active':g.active})
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	return res
	


def create_group(group_name, requester_email):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		res['code'] = msg_code['DUPLICATE_ERROR']
	except Group.DoesNotExist:
		group = Group(name=group_name, active=True)
		group.save()
		user = User(email = requester_email, group = group, admin = True, member = True)
		user.save()
		res['status'] = True
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	return res




def activate_group(group_name, requester_email):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		user = User.objects.get(email = requester_email, group = group, admin = True)
		group.active = True
		group.save()
		res['status'] = True
	except User.DoesNotExist:
		res['code'] = msg_code['PRIVILEGE_ERROR']
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	return res





def deactivate_group(group_name, requester_email):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		user = User.objects.get(email = requester_email, group = group, admin = True)
		group.active = False
		group.save()
		res['status'] = True
	except User.DoesNotExist:
		res['code'] = msg_code['PRIVILEGE_ERROR']
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	return res





def subscribe_group(group_name, requester_email):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name, active = True)
		user = User.objects.get(email = requester_email, group = group)
		user.member=True
		user.save()
		res['status'] = True
	except User.DoesNotExist:
		user = User(email = requester_email, group = group, member = True)
		user.save()
		res['status'] = True
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	return res




def unsubscribe_group(group_name, requester_email):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name, active = True)
		user = User.objects.get(email = requester_email, group = group)
		if(user.admin):
			res['code'] = msg_code['OWNER_UNSUBSCRIBE_ERROR']
		else:
			user.member=False
			user.save()
			res['status'] = True
	except User.DoesNotExist:
		res['status'] = True
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	return res




def get_group_info(group_name):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		members = User.objects.filter(group=group).values()
		res['status'] = True
		res['group_name'] = group_name
		res['active'] = group.active
		res['members'] = []   
		for member in members:
			for k,v in member.iteritems():
				res['members'].append({'name':str(k), 'active': v})
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']	
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	return res




def insert_post(group_name, message, poster_email):
	res = {'status':False}
	try:
		id = base64.b64encode(poster_email + str(time.time())).lower()
		p = Post(id = id, email = poster_email, subject = message['Subject'], post=str(message))
		p.save()
		f = Following(email = poster_email, post = p)
		f.save()
		res['status'] = True
		res['id'] = id
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	return res
	


def insert_reply(group_name, message, poster_email, post_id):
	res = {'status':False}
	try:
		id = base64.b64encode(poster_email + str(time.time())).lower()
		post = Post.objects.get(id=post_id)
		r = Post(id=id, email = poster_email, subject=message['Subject'], post = str(message), reply_to = post)
		r.save()
		res['status'] = True
		res['id'] = id
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	return res




def follow_post(post_id, requester_email):
	res = {'status':False}
	try:
		post = Post.objects.get(id=post_id)
		f = Following.objects.get(post = post, email=requester_email)
		res['status'] = True
	except Following.DoesNotExist:
		f = Following(post = post, email = requester_email)
		f.save()
		res['status'] = True
	except Post.DoesNotExist:
		res['code'] = msg_code['POST_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	return res





def unfollow_post(post_id, requester_email):
	res = {'status':False}
	try:
		post = Post.objects.get(id=post_id)
		f = Following.objects.get(post = post, email=requester_email)
		f.delete()
		res['status'] = True
	except Following.DoesNotExist:
		res['status'] = True
	except Post.DoesNotExist:
		res['code'] = msg_code['POST_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	return res











