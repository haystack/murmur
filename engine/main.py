import sys, logging, base64, email, datetime
from schema.models import *
from constants import *
from django.utils.timezone import utc
from django.db.models import Q
from browser.util import *
from lamson.mail import MailResponse
from smtp_handler.utils import relay_mailer
from bleach import clean
from cgi import escape
import re

from http_handler.settings import BASE_URL
import json
from engine.constants import extract_hash_tags


def list_groups(user=None):
	groups = []
	pub_groups = Group.objects.filter(Q(public=True, active=True)).order_by('name')
	for g in pub_groups:
		admin = False
		mod = False
		member = False
		
		if user != None:
			membergroup = MemberGroup.objects.filter(member=user, group=g)
			if membergroup.count() == 1:
				member = True
				admin = membergroup[0].admin
				mod = membergroup[0].moderator
			
		groups.append({'name':g.name, 
					   'desc': escape(g.description), 
					   'member': member, 
					   'admin': admin, 
					   'mod': mod,
					   'created': g.timestamp,
					   'count': g.membergroup_set.count()
					   })
	return groups


def group_info_page(user, group_name):
	res = {}
	try:
		group = Group.objects.get(name=group_name)
		members = MemberGroup.objects.filter(group=group)

		res['group'] = group
		res['members'] = []
		
		res['admin'] = False
		res['moderator'] = False
		res['subscribed'] = False
		
		for membergroup in members:
			
			if user != None:
				if user.email == membergroup.member.email:
					res['admin'] = membergroup.admin
					res['moderator'] = membergroup.moderator
					res['subscribed'] = True
			
			member_info = {'id':membergroup.id,
							'email': membergroup.member.email,
						   'joined': membergroup.timestamp,
						   'admin': membergroup.admin, 
						   'mod': membergroup.moderator}
			
			res['members'].append(member_info)
	except:
		res['group'] = None
	
	return res

def list_my_groups(user):
	res = {'status':False}
	try:
		membergroup = MemberGroup.objects.filter(member=user, group__active=True).select_related()
		res['status'] = True
		res['groups'] = []
		for mg in membergroup:
			res['groups'].append({'name':mg.group.name, 
								  'desc': escape(mg.group.description), 
								  'admin': mg.admin, 
								  'mod': mg.moderator})
			
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res
	


def create_group(group_name, group_desc, public, attach, requester):
	res = {'status':False}
	
	
	if not re.match('^[\w-]+$', group_name) is not None:
		res['code'] = msg_code['INCORRECT_GROUP_NAME']
		return res
	
	if len(group_desc) > MAX_GROUP_DESC_LENGTH:
		res['code'] = msg_code['MAX_GROUP_DESC_LENGTH']
		return res
	
	if len(group_name) > MAX_GROUP_NAME_LENGTH or len(group_name) == 0:
		res['code'] = msg_code['MAX_GROUP_NAME_LENGTH']
		return res
	
	try:
		group = Group.objects.get(name=group_name)
		res['code'] = msg_code['DUPLICATE_ERROR']
		
	except Group.DoesNotExist:
		group = Group(name=group_name, active=True, public=public, allow_attachments=attach, description=group_desc)
		group.save()
		
		membergroup = MemberGroup(group=group, member=requester, admin=True, moderator=True)
		membergroup.save()
		
		res['status'] = True
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
		
	logging.debug(res)
	return res

def edit_group_info(old_group_name, new_group_name, group_desc, public, attach, user):
	res = {'status':False}	
	try:
		group = Group.objects.get(name=old_group_name)
		group.name = new_group_name
		group.description = group_desc
		group.public = public
		group.allow_attachments = attach
		group.save()
		res['status'] = True	
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res


def get_group_settings(group_name, user):
	res = {'status':False}
	
	try:
		group = Group.objects.get(name=group_name)
		membergroup = MemberGroup.objects.get(group=group, member=user)
		res['following'] = membergroup.always_follow_thread
		res['no_emails'] = membergroup.no_emails
		res['status'] = True
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except MemberGroup.DoesNotExist:
		res['code'] = msg_code['NOT_MEMBER']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
		
	logging.debug(res)
	return res


def edit_group_settings(group_name, following, no_emails, user):
	res = {'status':False}
	
	try:
		group = Group.objects.get(name=group_name)
		membergroup = MemberGroup.objects.get(group=group, member=user)
		membergroup.always_follow_thread = following
		membergroup.no_emails = no_emails
		membergroup.save()
		
		res['status'] = True
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except MemberGroup.DoesNotExist:
		res['code'] = msg_code['NOT_MEMBER']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	
	logging.debug(res)
	return res




def activate_group(group_name, user):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		membergroup = MemberGroup.objects.get(group=group, member=user)
		if membergroup.admin:
			group.active = True
			group.save()
			res['status'] = True
		else:
			res['code'] = msg_code['PRIVILEGE_ERROR']
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except MemberGroup.DoesNotExist:
		res['code'] = msg_code['NOT_MEMBER']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res





def deactivate_group(group_name, user):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		membergroup = MemberGroup.objects.get(group=group, member=user)
		if membergroup.admin:
			group.active = False
			group.save()
			res['status'] = True
		else:
			res['code'] = msg_code['PRIVILEGE_ERROR']
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except MemberGroup.DoesNotExist:
		res['code'] = msg_code['NOT_MEMBER']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res

def edit_members_table(group_name, toDelete, toAdmin, toMod, user):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		membergroups = MemberGroup.objects.filter(group=group).select_related()
		toDelete_list = toDelete.split(',')
		toAdmin_list = toAdmin.split(',')
		toMod_list = toMod.split(',')
		toDelete_realList = []
		toAdmin_realList = []
		toMod_realList = []
		for item in toDelete_list:
			if item == '':
				continue
			else:
				toDelete_realList.append(int(item))
		for item in toAdmin_list:
			if item == '':
				continue
			else:
				toAdmin_realList.append(int(item))
		for item in toMod_list:
			if item == '':
				continue
			else:
				toMod_realList.append(int(item))
		for membergroup in membergroups:
			if membergroup.id in toDelete_realList:
				membergroup.delete()
		for membergroup in membergroups:
			if membergroup.id in toAdmin_realList:
				membergroup.admin = True
				membergroup.save()
		for membergroup in membergroups:
			if membergroup.id in toMod_realList:
				membergroup.moderator = True
				membergroup.save()
		res['status'] = True
	except Exception, e:
		print e
		logging.debug(e)
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res

def add_members(group_name, emails, user):
	res = {'status':False}
	
	try:
		group = Group.objects.get(name=group_name)
		membergroup = MemberGroup.objects.get(group=group, member=user)
		if membergroup.admin:
			email_list = emails.strip().lower().split(',')
			for email in email_list:
				email = email.strip()
				
				mail = MailResponse(From = 'no-reply@murmur.csail.mit.edu', 
									To = email, 
									Subject  = "You've been subscribed to %s Mailing List" % (group_name))
				
				email_user = UserProfile.objects.filter(email=email)
				if email_user.count() == 1:
					_ = MemberGroup.objects.get_or_create(member=email_user[0], group=group)
					
					message = "You've been subscribed to %s Mailing List. <br />" % (group_name)
					message += "To see posts from this list, visit <a href='%s/posts?group_name=%s'>%s/posts?group_name=%s</a><br />" % (BASE_URL, group_name, BASE_URL, group_name)
					message += "To manage your mailing list settings, subscribe, or unsubscribe, visit <a href='%s/groups/%s'>%s/groups/%s</a><br />" % (BASE_URL, group_name, BASE_URL, group_name)
				else:
					pw = password_generator()
					new_user = UserProfile.objects.create_user(email, pw)
					_ = MemberGroup.objects.get_or_create(group=group, member=new_user)
					
					message = "You've been subscribed to %s Mailing List. <br />" % (group_name)
					message += "An account has been created for you at <a href='%s'>%s</a><br />" % (BASE_URL, BASE_URL)
					message += "Your username is your email, which is %s and your auto-generated password is %s <br />" % (email, pw)
					message += "If you would like to change your password, please log in at the link above and then you can change it under your settings. <br />"
					message += "To see posts from this list, visit <a href='%s/posts?group_name=%s'>%s/posts?group_name=%s</a><br />" % (BASE_URL, group_name, BASE_URL, group_name)
					message += "To manage your mailing lists, subscribe, or unsubscribe from groups, visit <a href='%s/groups'>%s/groups</a><br />" % (BASE_URL, BASE_URL)

				mail.Html = message
				logging.debug('TO LIST: ' + str(email))
				
				relay_mailer.deliver(mail, To = [email])
			res['status'] = True
		else:
			res['code'] = msg_code['PRIVILEGE_ERROR']
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except MemberGroup.DoesNotExist:
		res['code'] = msg_code['NOT_MEMBER']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res




def subscribe_group(group_name, user):
	res = {'status':False}

	try:
		membergroup = MemberGroup.objects.filter(group__name=group_name, member=user)
		if membergroup.count() == 1:
			user.active=True
			user.save()
			res['status'] = True
		else:
			group = Group.objects.get(name=group_name)
			_ = MemberGroup.objects.create(group=group, member=user)
			res['status'] = True
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res




def unsubscribe_group(group_name, user):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		membergroup = MemberGroup.objects.get(group=group, member=user)
		membergroup.delete()
		res['status'] = True
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except MemberGroup.DoesNotExist:
		res['code'] = msg_code['NOT_MEMBER']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res

def group_info(group_name, user):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		membergroups = MemberGroup.objects.filter(group=group).select_related()
		
		res['status'] = True
		res['group_name'] = group_name
		res['active'] = group.active
		res['public'] = group.public
		res['allow_attachments'] = group.allow_attachments
		res['members'] = []
		for membergroup in membergroups:

			admin = membergroup.admin
			mod = membergroup.moderator
			
			if user.email == membergroup.member.email:
				res['admin'] = admin
				res['moderator'] = mod
				res['subscribed'] = True
			
			member_info = {'id': membergroup.id,
						   'email': membergroup.member.email,
						   'group_name': group_name, 
						   'admin': admin, 
						   'member': True, 
						   'moderator': mod, 
						   'active': membergroup.member.is_active}
			
			res['members'].append(member_info)
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']	
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res

def check_admin(user, groups):
	res = []
	try:
		for group in groups:
			group_name = group['name']
			group = Group.objects.get(name=group_name)
			membergroups = MemberGroup.objects.filter(group=group).select_related()
			for membergroup in membergroups:
				admin = membergroup.admin
				if user.email == membergroup.member.email:
					res.append({'name':group_name, 'admin':admin})

	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res

def format_date_time(d):
	return datetime.datetime.strftime(d, '%Y/%m/%d %H:%M:%S')

def list_posts(group_name=None, user=None, timestamp_str=None, return_replies=True, format_datetime=True):
	res = {'status':False}
	try:
		t = datetime.datetime.min
		if(timestamp_str):
			t = datetime.datetime.strptime(timestamp_str, '%Y/%m/%d %H:%M:%S')
		t = t.replace(tzinfo=utc, second = t.second + 1)
		
		if (group_name != None):
			g = Group.objects.filter(name=group_name)
			threads = Thread.objects.filter(timestamp__gt = t, group = g)
		else:
			threads = Thread.objects.filter(timestamp__gt = t)
		res['threads'] = []
		for t in threads:
			following = False
			muting = False
			
			if user:
				u = UserProfile.objects.get(email=user)
				following = Following.objects.filter(thread=t, user=u).exists()
				muting = Mute.objects.filter(thread=t, user=u).exists()
				
				member_group = MemberGroup.objects.filter(member=u, group=g)
				if member_group.exists():
					res['member_group'] = {'no_emails': member_group[0].no_emails, 
										   'always_follow_thread': member_group[0].always_follow_thread}

			posts = Post.objects.filter(thread = t).select_related()
			replies = []
			post = None
			thread_likes = 0
			
			for p in posts:
				post_likes = p.upvote_set.count()
				user_liked = False
				if user:
					user_liked = p.upvote_set.filter(user=u).exists()
				thread_likes += post_likes
				post_dict = {'id': p.id,
							'msg_id': p.msg_id, 
							'thread_id': p.thread_id, 
							'from': p.author.email, 
							'to': p.group.name, 
							'subject': escape(p.subject),
							'likes': post_likes, 
							'liked': user_liked,
							'text': clean(p.post, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, styles=ALLOWED_STYLES), 
							'timestamp': format_date_time(p.timestamp) if format_datetime else p.timestamp}
				if not p.reply_to_id:
					post = post_dict
					if not return_replies:
						break
				else:
					replies.append(post_dict)
			tags = list(Tag.objects.filter(tagthread__thread=t).values('name', 'color'))
			res['threads'].append({'thread_id': t.id, 
								   'post': post, 
								   'num_replies': posts.count() - 1,
								   'replies': replies, 
								   'following': following, 
								   'muting': muting,
								   'tags': tags,
								   'likes': thread_likes,
								   'timestamp': format_date_time(t.timestamp) if format_datetime else t.timestamp})
			res['status'] = True
			
	except Exception, e:
		print e
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res
	
def load_thread(t, user=None, member=None):

	following = False
	muting = False
	no_emails = False
	always_follow = False
	is_member = False
	total_likes = 0
	if user:
		following = Following.objects.filter(thread=t, user=user).exists()
		muting = Mute.objects.filter(thread=t, user=user).exists()
		if member:
			is_member = True
			no_emails = member.no_emails
			always_follow = member.always_follow_thread
	
	
	posts = Post.objects.filter(thread = t)		
	replies = []
	post = None
	for p in posts:
		post_likes = p.upvote_set.count()
		total_likes += post_likes
		user_liked = False
		if user:
			user_liked = p.upvote_set.filter(user=user).exists()
		post_dict = {
					'id': str(p.id),
					'msg_id': p.msg_id, 
					'thread_id': p.thread_id, 
					'from': p.author.email, 
					'likes': post_likes,
					'to': p.group.name, 
					'liked': user_liked,
					'subject': escape(p.subject), 
					'text': clean(p.post, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, styles=ALLOWED_STYLES), 
					'timestamp': p.timestamp
					}
		if not p.reply_to_id:
			post = post_dict
		else:
			replies.append(post_dict)
	tags = list(Tag.objects.filter(tagthread__thread=t).values('name', 'color'))
	
	return {'status': True,
			'thread_id': t.id, 
		    'post': post, 
		    'replies': replies, 
		    'tags': json.dumps(tags),
		    'following': following, 
		    'muting': muting,
		    'member': is_member,
		    'no_emails': no_emails,
		    'always_follow': always_follow,
		    'likes': total_likes,
		    'timestamp': t.timestamp}

def load_post(group_name, thread_id, msg_id):
	res = {'status':False}
	try:
		t = Thread.objects.get(id=thread_id)
		p = Post.objects.get(msg_id=msg_id, thread= t)
		tags = list(Tag.objects.filter(tagthread__thread=t).values('name', 'color'))
		res['status'] = True
		res['msg_id'] = p.msg_id
		res['thread_id'] = p.thread_id
		res['from'] = p.email
		res['tags'] = json.dumps(tags)
		res['subject'] = escape(p.subject)
		res['text'] = clean(p.post, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, styles=ALLOWED_STYLES)
		res['to'] = p.group.name
	except Thread.DoesNotExist:
		res['code'] = msg_code['THREAD_NOT_FOUND_ERROR']
	except Post.DoesNotExist:
		res['code'] = msg_code['POST_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res


def _create_tag(group, thread, name):
	t, created = Tag.objects.get_or_create(group=group, name=name)
	if created:
		r = lambda: random.randint(0,255)
		color = '%02X%02X%02X' % (r(),r(),r())
		t.color = color
		t.save()
	tagthread,_ = TagThread.objects.get_or_create(thread=thread, tag=t)

def _create_post(group, subject, message_text, user):

	try:
		message_text = message_text.decode("utf-8")
	except Exception, _:
		logging.debug("guessing this is unicode then")
	
	message_text = message_text.encode("ascii", "ignore")
	
	stripped_subj = re.sub("\[.*?\]", "", subject).strip()
	
	thread = Thread()
	thread.subject = stripped_subj
	thread.group = group
	thread.save()
	

	msg_id = base64.b64encode(user.email + str(datetime.datetime.now())).lower() + '@murmur.csail.mit.edu'
	
	p = Post(msg_id=msg_id, author=user, subject=stripped_subj, post=message_text, group=group, thread=thread)
	p.save()
	
	
	for match in re.findall(r"[^[]*\[([^]]*)\]", subject):
		if match.lower() != group.name:
			_create_tag(group, thread, match)
	
	tags = list(extract_hash_tags(message_text))
	for tag in tags:
		if tag.lower() != group.name:
			_create_tag(group, thread, tag)
	
	tag_objs = Tag.objects.filter(tagthread__thread=thread)
	tags = list(tag_objs.values('name', 'color'))
	
	f = Following(user=user, thread=thread)
	f.save()
	
	
	group_members = MemberGroup.objects.filter(group=group)
	
	recipients = []
	for m in group_members:
		if not m.no_emails and m.member.email != user.email:
			mute_tag = MuteTag.objects.filter(tag__in=tag_objs, group=group, user=m.member).exists()
			if not mute_tag:
				recipients.append(m.member.email)
		else:
			follow_tag = FollowTag.objects.filter(tag__in=tag_objs, group=group, user=m.member).exists()
			if follow_tag:
				recipients.append(m.member.email)
				
	recipients.append(user.email)
	
	return p, thread, recipients, tags, tag_objs

def insert_post_web(group_name, subject, message_text, user):
	res = {'status':False}
	thread = None
	
	try:
		group = Group.objects.get(name=group_name)
		user_member = MemberGroup.objects.filter(group=group, member=user)
		if user_member.exists():
			p, thread, recipients, tags, tag_objs = _create_post(group, subject, message_text, user)
			res['status'] = True
			
			res['member_group'] = {'no_emails': user_member[0].no_emails, 
								   'always_follow_thread': user_member[0].always_follow_thread}
	
			post_info = {'msg_id': p.msg_id,
						 'thread_id': thread.id,
						 'from': user.email,
						 'to': group_name,
						 'subject': escape(p.subject),
						 'text': clean(p.post, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, styles=ALLOWED_STYLES), 
						 'timestamp': format_date_time(p.timestamp),
						}
				
			res['threads'] = []
			res['threads'].append({'thread_id': thread.id,
								   'post': post_info,
								   'num_replies': 0,
								   'replies': [],
								   'following': True,
								   'muting': False,
								   'tags': tags,
								   'timestamp': format_date_time(p.timestamp)})
			res['msg_id'] = p.msg_id
			res['thread_id'] = thread.id
			res['post_id'] = p.id
			res['tags'] = tags
			res['tag_objs'] = tag_objs
			res['recipients'] = recipients
		else:
			res['code'] = msg_code['NOT_MEMBER']
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except Exception, e:
		print e
		logging.debug(e)
		if(thread and thread.id):
			thread.delete()
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res


def insert_post(group_name, subject, message_text, user):
	res = {'status':False}
	thread = None
	try:
		group = Group.objects.get(name=group_name)
		user_member = MemberGroup.objects.filter(group=group, member=user)
		if user_member.exists():
			p, thread, recipients, tags, tag_objs = _create_post(group, subject, message_text, user)
			res['status'] = True
			res['post_id'] = p.id
			res['msg_id'] = p.msg_id
			res['thread_id'] = thread.id
			res['tags'] = tags
			res['tag_objs'] = tag_objs
			res['recipients'] = recipients
		else:
			res['code'] = msg_code['NOT_MEMBER']

	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except Exception, e:
		print e
		logging.debug(e)
		if(thread and thread.id):
			thread.delete()
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res
	


def insert_reply(group_name, subject, message_text, user, thread_id=None):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		
		group_members = UserProfile.objects.filter(membergroup__group=group)
		
		if user in group_members:
			
			orig_post_subj = subject[4:].strip()
			
			post = Post.objects.filter(Q(subject=orig_post_subj) | Q(subject=subject)).order_by('-timestamp')
			if post.count() >= 1:
				post = post[0]
			else:
				post = None
				
			if not thread_id:
				thread = Thread.objects.filter(subject=orig_post_subj).order_by('-timestamp')
				if thread.count() == 1:
					thread = thread[0]
				else:
					thread = None
			else:
				thread = Thread.objects.filter(id=thread_id)
				if thread.count() == 1:
					thread = thread[0]
				else:
					thread = None
			
			if not thread:
				thread = Thread()
				thread.subject = orig_post_subj
				thread.group = group
				thread.save()
			
			tag_objs = Tag.objects.filter(tagthread__thread=thread)
			
			msg_id = base64.b64encode(user.email + str(datetime.datetime.now())).lower() + '@murmur.csail.mit.edu'
			
			try:
				message_text = message_text.decode("utf-8")
			except Exception, e:
				logging.debug("guessing this is unicode then")
			
			message_text = message_text.encode("ascii", "ignore")
			
			r = Post(msg_id=msg_id, author=user, subject=subject, post = message_text, reply_to=post, group=group, thread=thread)
			r.save()
			
			thread.timestamp = datetime.datetime.now().replace(tzinfo=utc)
			thread.save()
			
			if not Following.objects.filter(user=user, thread=thread).exists(): 
				f = Following(user=user, thread=thread)
				f.save()
				
				
			member_recip = MemberGroup.objects.filter(group=group, always_follow_thread=True, no_emails=False)
			always_follow_members = [member_group.member.email for member_group in member_recip]
			
			#users that have muted the thread and are set to always follow
			muted = Mute.objects.filter(thread=thread).select_related()
			muted_emails = [m.user.email for m in muted if m.user.email in always_follow_members]
			
			#users following the thread and set to not always follow
			following = Following.objects.filter(thread=thread)
			recipients = [f.user.email for f in following if f.user.email not in always_follow_members]
			
			if tag_objs.count() > 0:
				#users muting the tag and are set to always follow
				muted_tag = MuteTag.objects.filter(group=group, tag__in=tag_objs).select_related()
				muted_emails.extend([m.user.email for m in muted_tag if m.user.email in always_follow_members])

				#users following the tag
				follow_tag = FollowTag.objects.filter(group=group, tag__in=tag_objs).select_related()
				recipients.extend([f.user.email for f in follow_tag if f.user.email not in always_follow_members])
			
			#users that always follow threads in this group. minus those that muted
			recipients.extend([m.member.email for m in member_recip if m.member.email not in muted_emails])
			
			res['status'] = True
			res['recipients'] = list(set(recipients))
			res['tags'] = list(tag_objs.values('name'))
			res['tag_objs'] = tag_objs
			res['thread_id'] = thread.id
			res['msg_id'] = msg_id
			res['post_id'] = r.id
			
		else:
			res['code'] = msg_code['NOT_MEMBER']
		
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except Post.DoesNotExist:
		res['code'] = msg_code['POST_NOT_FOUND_ERROR']
	except:
		logging.debug(sys.exc_info())
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res

def upvote(post_id, email=None, user=None):
	res = {'status':False}
	p = None
	try:
		if email:
			user = UserProfile.objects.get(email=email)
		p = Post.objects.get(id=int(post_id))
		l = Upvote.objects.get(post=p, user=user)
		res['status'] = True
		res['thread_id'] = p.thread.id
		res['post_name'] = p.subject
		res['post_id'] = p.id
		res['group_name'] = p.group.name
	except UserProfile.DoesNotExist:
		res['code'] = msg_code['USER_DOES_NOT_EXIST'] % email
	except Upvote.DoesNotExist:
		l = Upvote(post=p, user=user)
		l.save()
		res['status'] = True
		res['thread_id'] = p.thread.id
		res['post_name'] = p.subject
		res['post_id'] = p.id
		res['group_name'] = p.group.name
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res

def unupvote(post_id, email=None, user=None):
	res = {'status':False}
	p = None
	try:
		if email:
			user = UserProfile.objects.get(email=email)
		p = Post.objects.get(id=int(post_id))
		l = Upvote.objects.get(post=p, user=user)
		l.delete()
		res['status'] = True
		res['post_name'] = p.subject
		res['thread_id'] = p.thread.id
		res['post_id'] = p.id
		res['group_name'] = p.group.name
	except UserProfile.DoesNotExist:
		res['code'] = msg_code['USER_DOES_NOT_EXIST'] % email
	except Upvote.DoesNotExist:
		res['status'] = True
		res['thread_id'] = p.thread.id
		res['post_name'] = p.subject
		res['post_id'] = p.id
		res['group_name'] = p.group.name
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res

def follow_thread(thread_id, email=None, user=None):
	res = {'status':False}
	t = None
	try:
		if email:
			user = UserProfile.objects.get(email=email)
		t = Thread.objects.get(id=int(thread_id))
		f = Following.objects.get(thread=t, user=user)
		res['status'] = True
		res['thread_name'] = t.subject
		res['thread_id'] = t.id
		res['group_name'] = t.group.name
	except UserProfile.DoesNotExist:
		res['code'] = msg_code['USER_DOES_NOT_EXIST'] % email
	except Following.DoesNotExist:
		f = Following(thread=t, user=user)
		f.save()
		res['status'] = True
		res['thread_name'] = t.subject
		res['thread_id'] = t.id
		res['group_name'] = t.group.name
	except Thread.DoesNotExist:
		res['code'] = msg_code['THREAD_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res





def unfollow_thread(thread_id, email=None, user=None):
	res = {'status':False}
	try:
		if email:
			user = UserProfile.objects.get(email=email)
		t = Thread.objects.get(id=int(thread_id))
		f = Following.objects.filter(thread=t, user=user)
		f.delete()
		res['status'] = True
		res['thread_name'] = t.subject
		res['thread_id'] = t.id
		res['group_name'] = t.group.name
	except UserProfile.DoesNotExist:
		res['code'] = msg_code['USER_DOES_NOT_EXIST'] % email
	except Following.DoesNotExist:
		res['status'] = True
		res['thread_name'] = t.subject
		res['thread_id'] = t.id
		res['group_name'] = t.group.name
	except Thread.DoesNotExist:
		res['code'] = msg_code['THREAD_NOT_FOUND_ERROR']
	except Exception, e:
		print e
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res



def mute_thread(thread_id, email=None, user=None):
	res = {'status':False}
	t = None
	try:
		if email:
			user = UserProfile.objects.get(email=email)
		t = Thread.objects.get(id=int(thread_id))
		f = Mute.objects.get(thread=t, user=user)
		res['status'] = True
		res['thread_name'] = t.subject
		res['thread_id'] = t.id
		res['group_name'] = t.group.name
	except UserProfile.DoesNotExist:
		res['code'] = msg_code['USER_DOES_NOT_EXIST'] % email
	except Mute.DoesNotExist:
		f = Mute(thread=t, user=user)
		f.save()
		res['status'] = True
		res['thread_name'] = t.subject
		res['thread_id'] = t.id
		res['group_name'] = t.group.name
	except Thread.DoesNotExist:
		res['code'] = msg_code['THREAD_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res





def unmute_thread(thread_id, email=None, user=None):
	res = {'status':False}
	try:
		if email:
			user = UserProfile.objects.get(email=email)
		t = Thread.objects.get(id=int(thread_id))
		f = Mute.objects.filter(thread=t, user=user)
		f.delete()
		res['status'] = True
		res['thread_name'] = t.subject
		res['thread_id'] = t.id
		res['group_name'] = t.group.name
	except UserProfile.DoesNotExist:
		res['code'] = msg_code['USER_DOES_NOT_EXIST'] % email
	except Mute.DoesNotExist:
		res['status'] = True
		res['thread_name'] = t.subject
		res['thread_id'] = t.id
		res['group_name'] = t.group.name
	except Thread.DoesNotExist:
		res['code'] = msg_code['THREAD_NOT_FOUND_ERROR']
	except Exception, e:
		print e
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res


def follow_tag(tag_name, group_name, user=None, email=None):
	res = {'status':False}
	g = Group.objects.get(name=group_name)
	tag = None
	try:
		if email:
			user = UserProfile.objects.get(email=email)
		tag = Tag.objects.get(name=tag_name, group=g)
		tag_follow = FollowTag.objects.get(tag=tag, user=user)
		res['tag_name'] = tag_name
		res['status'] = True
	except FollowTag.DoesNotExist:
		f = FollowTag(tag=tag, group=g, user=user)
		f.save()
		res['tag_name'] = tag_name
		res['status'] = True
	except Tag.DoesNotExist:
		res['code'] = msg_code['TAG_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res



def unfollow_tag(tag_name, group_name, user=None, email=None):
	res = {'status':False}
	g = Group.objects.get(name=group_name)
	tag = None
	try:
		if email:
			user = UserProfile.objects.get(email=email)
		tag = Tag.objects.get(name=tag_name, group=g)
		tag_follow = FollowTag.objects.get(tag=tag, user=user)
		tag_follow.delete()
		res['tag_name'] = tag_name
		res['status'] = True
	except FollowTag.DoesNotExist:
		res['tag_name'] = tag_name
		res['status'] = True
	except Tag.DoesNotExist:
		res['code'] = msg_code['TAG_NOT_FOUND_ERROR']
	except Exception, e:
		print e
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res


def mute_tag(tag_name, group_name, user=None, email=None):
	res = {'status':False}
	g = Group.objects.get(name=group_name)
	tag = None
	try:
		if email:
			user = UserProfile.objects.get(email=email)
		tag = Tag.objects.get(name=tag_name, group=g)
		tag_mute = MuteTag.objects.get(tag=tag, user=user)
		res['tag_name'] = tag_name
		res['status'] = True
	except MuteTag.DoesNotExist:
		f = MuteTag(tag=tag, group=g, user=user)
		f.save()
		res['tag_name'] = tag_name
		res['status'] = True
	except Tag.DoesNotExist:
		res['code'] = msg_code['TAG_NOT_FOUND_ERROR']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res



def unmute_tag(tag_name, group_name, user=None, email=None):
	res = {'status':False}
	g = Group.objects.get(name=group_name)
	tag = None
	try:
		if email:
			user = UserProfile.objects.get(email=email)
		tag = Tag.objects.get(name=tag_name, group=g)
		tag_mute = MuteTag.objects.get(tag=tag, user=user)
		tag_mute.delete()
		res['tag_name'] = tag_name
		res['status'] = True
	except MuteTag.DoesNotExist:
		res['tag_name'] = tag_name
		res['status'] = True
	except Tag.DoesNotExist:
		res['code'] = msg_code['TAG_NOT_FOUND_ERROR']
	except Exception, e:
		print e
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res
