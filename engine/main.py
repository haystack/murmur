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
	logging.debug(res)
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
	logging.debug(res)
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
	logging.debug(res)
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
	logging.debug(res)
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
	logging.debug(res)
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
	logging.debug(res)
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
	logging.debug(res)
	return res



def list_posts(group_name=None):
	res = {'status':False}
	try:
		threads = Thread.objects.all()
		res['status'] = True
		res['threads'] = []
		for t in threads:
			posts = Post.objects.filter(thread = t)		
			t_posts = []
			blurb = None
			for p in posts:
				if(not p.reply_to_id):
					blurb = {'msg_id':p.msg_id, 'thread_id':p.thread_id, 'from':p.email, 'to':p.group.name, 'subject':p.subject, 'text': p.post}
				t_posts.append({'msg_id':p.msg_id, 'thread_id':p.thread_id, 'from':p.email, 'to':p.group.name, 'subject':p.subject, 'text': p.post})
			res['threads'].append({'id':t.id, 'posts':t_posts, 'blurb': blurb})
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res
	

def load_post(group_name, thread_id, msg_id):
	res = {'status':False}
	try:
		t = Thread.objects.get(id=thread_id)
		p = Post.objects.get(msg_id=msg_id, thread= t)
		res['status'] = True
		res['msg_id'] = p.msg_id
		res['thread_id'] = p.thread_id
		res['from'] = p.email
		res['subject'] = p.subject
		res['text'] = p.post
		res['to'] = p.group.name
	except Thread.DoesNotExist:
		res['code'] = msg_code['THREAD_NOT_FOUND_ERROR']
	except Post.DoesNotExist:
		res['code'] = msg_code['POST_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res


def insert_post(group_name, subject, message_text, poster_email):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		group_members = User.objects.filter(group = group, active = True)
		recipients = [m.email for m in group_members]
		thread = Thread()
		thread.save()
		msg_id = base64.b64encode(poster_email + str(time.time())).lower()
		p = Post(msg_id = msg_id, email = poster_email, subject = subject, post=str(message_text), group = group, thread=thread)
		p.save()
		f = Following(email = poster_email, thread = thread)
		f.save()
		res['status'] = True
		res['msg_id'] = msg_id
		res['thread_id'] = thread.id
		res['recipients'] = recipients
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res
	


def insert_reply(group_name, subject, message_text, poster_email, msg_id, thread_id):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		post = Post.objects.get(msg_id=msg_id)
		thread = Thread.objects.get(id=thread_id)
		new_msg_id = base64.b64encode(poster_email + str(time.time())).lower()
		r = Post(msg_id=new_msg_id, email = poster_email, subject=subject, post = str(message_text), reply_to = post, group = group, thread=thread)
		r.save()
		following = Following.objects.filter(thread = thread)
		recipients = [f.email for f in following]
		res['status'] = True
		res['msg_id'] = new_msg_id
		res['thread_id'] = thread.id
		res['recipients'] = recipients
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except Post.DoesNotExist:
		res['code'] = msg_code['POST_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res




def follow_thread(thread_id, requester_email):
	res = {'status':False}
	t = None
	try:
		t = Thread.objects.get(id=thread_id)
		f = Following.objects.get(thread = t, email=requester_email)
		res['status'] = True
	except Following.DoesNotExist:
		f = Following(thread = t, email = requester_email)
		f.save()
		res['status'] = True
	except Thread.DoesNotExist:
		res['code'] = msg_code['THREAD_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res





def unfollow_thread(thread_id, requester_email):
	res = {'status':False}
	try:
		t = Thread.objects.get(id=thread_id)
		f = Following.objects.get(thread = t, email=requester_email)
		f.delete()
		res['status'] = True
	except Following.DoesNotExist:
		res['status'] = True
	except Thread.DoesNotExist:
		res['code'] = msg_code['THREAD_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res











