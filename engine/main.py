import logging, time, base64, email
from schema.models import *
from msg_codes import *

'''
MailX Main Controller

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''

def list_groups():
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
		user = User(email = requester_email, group = group, admin = True, active = True)
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
	group = None
	try:
		group = Group.objects.get(name=group_name, active = True)
		user = User.objects.get(email = requester_email, group = group)
		user.active=True
		user.save()
		res['status'] = True
	except User.DoesNotExist:
		user = User(email = requester_email, group = group, active = True)
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
			user.active=False
			user.save()
			res['status'] = True
	except User.DoesNotExist:
		res['status'] = True
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	return res




def group_info(group_name):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		members = User.objects.filter(group=group).values()
		res['status'] = True
		res['group_name'] = group_name
		res['active'] = group.active
		res['members'] = []
		for member in members:
			res['members'].append({'email': member['email'], 'group_name':group_name, 'admin': member['admin'], 'member':member['member'], 'moderator':member['moderator'], 'guest':member['guest'], 'active':member['active']})
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']	
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	return res



def list_posts(group_name=None):
	res = {'status':False}
	try:
		posts = Post.objects.all()
		res['status'] = True
		res['posts'] = []
		for p in posts:
			res['posts'].append({'id':p.id, 'from':p.email, 'to':p.group.name, 'subject':p.subject})
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	return res
	

def load_post(group_name, post_id):
	res = {'status':False}
	try:
		p = Post.objects.get(id=post_id)
		res['status'] = True
		res['id'] = p.id
		res['from'] = p.email
		res['subject'] = p.subject
		res['text'] = p.post
		res['to'] = p.group.name
	except Post.DoesNotExist:
		res['code'] = msg_code['POST_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	return res


def insert_post(group_name, subject, message_text, poster_email):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		group_members = User.objects.filter(group = group, active = True)
		recipients = [m.email for m in group_members]
		id = base64.b64encode(poster_email + str(time.time())).lower()
		p = Post(id = id, email = poster_email, subject = subject, post=str(message_text), group = group)
		p.save()
		f = Following(email = poster_email, post = p)
		f.save()
		res['status'] = True
		res['id'] = id
		res['recipients'] = recipients
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	return res
	


def insert_reply(group_name, subject, message_text, poster_email, post_id):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		id = base64.b64encode(poster_email + str(time.time())).lower()
		post = Post.objects.get(id=post_id)
		r = Post(id=id, email = poster_email, subject=subject, post = str(message_text), reply_to = post, group = group)
		r.save()
		following = Following.objects.filter(post = post)
		recipients = [f.email for f in following]
		res['status'] = True
		res['id'] = id
		res['recipients'] = recipients
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except Post.DoesNotExist:
		res['code'] = msg_code['POST_NOT_FOUND_ERROR']
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











