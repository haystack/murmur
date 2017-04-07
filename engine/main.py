import sys, logging, base64, email, datetime
from schema.models import *
from constants import *
from django.utils.timezone import utc
from django.db.models import Q
from browser.util import *
from lamson.mail import MailResponse
from smtp_handler.utils import relay_mailer, NO_REPLY
from bleach import clean
from cgi import escape
from attachments import upload_attachments
import re
import hashlib
import random

from http_handler.settings import BASE_URL, WEBSITE, AWS_STORAGE_BUCKET_NAME
import json
from engine.constants import extract_hash_tags, ALLOWED_MESSAGE_STATUSES


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
		members_pending = MemberGroupPending.objects.filter(group=group)

		res['group'] = group
		res['members'] = []
		res['members_pending'] = []
		res['lists'] = []
		
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

		for membergroup in members_pending:
			member_info = {'id':membergroup.id,
							'email': membergroup.member.email,
						   'admin': False,
						   'mod': False}
			res['members_pending'].append(member_info)

		lists = ForwardingList.objects.filter(group=group)

		for l in lists:
			list_obj = {'id' : l.id,
						'email' : l.email,
						'can_post' : l.can_post,
						'can_receive' : l.can_receive,
						'added': l.timestamp,
						'url' : l.url
						}
			res['lists'].append(list_obj)


	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
		res['group'] = None

	except Exception, e:
		res['code'] = msg_code['UNKNOWN_ERROR']
		logging.debug(e)
	
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
		def email_on_role_change(type, group, email):
			if type == "delete":
				subject = "removed from the group"
			elif type == "admin":
				subject = "made an admin in group"
			elif type == "mod":
				subject = "made a moderator in group"
			mail = MailResponse(From = NO_REPLY, To = email, Subject = "You've been " + subject + " " + group, Html = "You've been " + subject + " " + group + "<br /><br />To manage your mailing lists, subscribe, or unsubscribe from groups, visit <a href='http://%s/groups'>http://%s/my_groups</a>" % (BASE_URL, BASE_URL))
			relay_mailer.deliver(mail, To = [email])
		for membergroup in membergroups:
			if membergroup.id in toDelete_realList:
				membergroup.delete()
				email_on_role_change("delete", membergroup.group.name, membergroup.member.email)
		for membergroup in membergroups:
			if membergroup.id in toAdmin_realList:
				membergroup.admin = True
				membergroup.save()
				email_on_role_change("admin", membergroup.group.name, membergroup.member.email)
		for membergroup in membergroups:
			if membergroup.id in toMod_realList:
				membergroup.moderator = True
				membergroup.save()
				email_on_role_change("mod", membergroup.group.name, membergroup.member.email)
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
		if len(new_group_name) > 0:
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
		res['upvote_emails'] = membergroup.upvote_emails
		res['receive_attachments'] = membergroup.receive_attachments
		res['status'] = True
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except MemberGroup.DoesNotExist:
		res['code'] = msg_code['NOT_MEMBER']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
		
	logging.debug(res)
	return res

def edit_group_settings(group_name, following, upvote_emails, receive_attachments, no_emails, user):
	res = {'status':False}
	
	try:
		group = Group.objects.get(name=group_name)
		membergroup = MemberGroup.objects.get(group=group, member=user)
		membergroup.always_follow_thread = following
		membergroup.upvote_emails = upvote_emails
		membergroup.receive_attachments = receive_attachments
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

def delete_group(group_name, user):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		membergroup = MemberGroup.objects.get(group=group, member=user)
		if membergroup.admin:
			group.delete()
			res['status'] = True
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except MemberGroup.DoesNotExist:
		res['code'] = msg_code['NOT_MEMBER']
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res

def add_list(group_name, email, can_receive, can_post, list_url, user):

	res = {'status' : False }

	try:
		group = Group.objects.get(name=group_name)
		membergroup = MemberGroup.objects.get(group=group, member=user)

		if membergroup.admin:
			email = email.strip()
			list_url = list_url.strip()
			f = ForwardingList(group=group, email=email, url=list_url, can_receive = can_receive, can_post = can_post)
			f.save()
			res['status'] = True
		else:
			res['code'] = msg_code['PRIVILEGE_ERROR']
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except MemberGroup.DoesNotExist:
		res['code'] = msg_code['NOT_MEMBER']
	except Exception, e:
		res['error'] = e
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res

def delete_list(group_name, emails, user):
	res = {'status' : False}
	try:
		group = Group.objects.get(name=group_name)
		membergroup = MemberGroup.objects.get(group=group, member=user)
		if membergroup.admin:
			for email in emails.split(','):
				f = ForwardingList.objects.get(group=group, email=email)
				f.delete()
			res['status'] = True
		else:
			res['code'] = msg_code['PRIVILEGE_ERROR']
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except MemberGroup.DoesNotExist:
		res['code'] = msg_code['NOT_MEMBER']
	except Exception, e:
		res['error'] = e
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res

def adjust_list_can_post(group_name, emails, can_post, user):
	res = {'status' : False}
	try:
		group = Group.objects.get(name=group_name)
		membergroup = MemberGroup.objects.get(group=group, member=user)
		if membergroup.admin:
			for email in emails.split(','):
				f = ForwardingList.objects.get(group=group, email=email)
				f.can_post = can_post
				f.save()
			res['status'] = True
		else:
			res['code'] = msg_code['PRIVILEGE_ERROR']
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except MemberGroup.DoesNotExist:
		res['code'] = msg_code['NOT_MEMBER']
	except Exception, e:
		res['error'] = e
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res

def adjust_list_can_receive(group_name, emails, can_receive, user):

	res = {'status' : False}
	try:
		group = Group.objects.get(name=group_name)
		membergroup = MemberGroup.objects.get(group=group, member=user)
		if membergroup.admin:
			for email in emails.split(','):
				f = ForwardingList.objects.get(group=group, email=email)
				f.can_receive = can_receive
				f.save()
			res['status'] = True
		else:
			res['code'] = msg_code['PRIVILEGE_ERROR']
	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
	except MemberGroup.DoesNotExist:
		res['code'] = msg_code['NOT_MEMBER']
	except Exception, e:
		res['error'] = e
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res

def add_members(group_name, emails, add_as_mods, user):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		is_public = group.public
		is_admin = False
		if user:
			membergroup = MemberGroup.objects.get(group=group, member=user)
			is_admin = membergroup.admin
		if is_public or is_admin:
			email_list = emails.strip().lower().split(',')

			for address in email_list:
				e = address.strip()
				logging.debug("address: " + e)
				match = re.match(r'[\S]+@[\S]+\.[\S]+', e)
				logging.debug("match: " + match)
				if not re.match(r'[\S]+@[\S]+\.[\S]+', e):
					res['code'] = msg_code['REQUEST_ERROR']
					res['error'] = "Improperly formatted email address"
					return res

			for email in email_list:
				email = email.strip()
				
				email_user = UserProfile.objects.filter(email=email)
				member = False
				if email_user.count() == 1:
					member = MemberGroup.objects.filter(member=email_user[0], group=group).exists() or MemberGroupPending.objects.filter(member=email_user[0], group=group).exists()
				if not member:
					confirm_code = hashlib.sha1(email+group_name+str(random.random())).hexdigest()
					confirm_url = 'http://' + BASE_URL + '/subscribe/confirm/' + confirm_code
					if WEBSITE == "murmur":
						mail = MailResponse(From = NO_REPLY, 
											To = email, 
											Subject  = "You've been invited to join %s Mailing List" % (group_name))
						
						if email_user.count() == 1:
							mg,_ = MemberGroupPending.objects.get_or_create(member=email_user[0], group=group, hash=confirm_code)
							message = "You've been invited to join %s Mailing List. <br />" % (group_name)
							message += "To confirm your subscription to this list, visit <a href='%s'>%s</a><br />" % (confirm_url, confirm_url)
							message += "To see posts from this list, visit <a href='http://%s/posts?group_name=%s'>http://%s/posts?group_name=%s</a><br />" % (BASE_URL, group_name, BASE_URL, group_name)
							message += "To manage your mailing list settings, subscribe, or unsubscribe, visit <a href='http://%s/groups/%s'>http://%s/groups/%s</a><br />" % (BASE_URL, group_name, BASE_URL, group_name)
						else:
							pw = password_generator()
							new_user = UserProfile.objects.create_user(email, pw)
							mg,_ = MemberGroupPending.objects.get_or_create(group=group, member=new_user, hash=confirm_code)
							message = "You've been subscribed to %s Mailing List. <br />" % (group_name)
							message += "To confirm your subscription to this list, visit <a href='%s'>%s</a><br />" % (confirm_url, confirm_url)
							message += "An account to manage your settings has been created for you at <a href='http://%s'>http://%s</a><br />" % (BASE_URL, BASE_URL)
							message += "Your username is your email, which is %s and your auto-generated password is %s <br />" % (email, pw)
							message += "If you would like to change your password, please log in at the link above and then you can change it under your settings. <br />"
							message += "To see posts from this list, visit <a href='http://%s/posts?group_name=%s'>http://%s/posts?group_name=%s</a><br />" % (BASE_URL, group_name, BASE_URL, group_name)
							message += "To manage your mailing lists, subscribe, or unsubscribe from groups, visit <a href='http://%s/groups'>http://%s/my_groups</a><br />" % (BASE_URL, BASE_URL)
		
						mail.Html = message
						logging.debug('TO LIST: ' + str(email))
					elif WEBSITE == "squadbox":
						mail = MailResponse(From = NO_REPLY, 
											To = email, 
											Subject  = "You've been invited to join %s squad" % (group_name))
						
						if email_user.count() == 1:
							mg,_ = MemberGroupPending.objects.get_or_create(member=email_user[0], group=group, hash=confirm_code)
							message = "You've been invited to join %s squad. <br />" % (group_name)
							message += "To confirm your membership of this squad, visit <a href='%s'>%s</a><br />" % (confirm_url, confirm_url)
							message += "To see posts for this squad, visit <a href='http://%s/posts?group_name=%s'>http://%s/posts?group_name=%s</a><br />" % (BASE_URL, group_name, BASE_URL, group_name)
							message += "To manage your squad settings, subscribe, or unsubscribe, visit <a href='http://%s/groups/%s'>http://%s/groups/%s</a><br />" % (BASE_URL, group_name, BASE_URL, group_name)
						else:
							pw = password_generator()
							new_user = UserProfile.objects.create_user(email, pw)
							mg,_ = MemberGroupPending.objects.get_or_create(group=group, member=new_user, hash=confirm_code)
							message = "You've been added as a moderator to %s squad. <br />" % (group_name)
							message += "To confirm your membership of this squad, visit <a href='%s'>%s</a><br />" % (confirm_url, confirm_url)
							message += "An account to manage your settings has been created for you at <a href='http://%s'>http://%s</a><br />" % (BASE_URL, BASE_URL)
							message += "Your username is your email, which is %s and your auto-generated password is %s <br />" % (email, pw)
							message += "If you would like to change your password, please log in at the link above and then you can change it under your settings. <br />"
							message += "To see posts from this squad, visit <a href='http://%s/posts?group_name=%s'>http://%s/posts?group_name=%s</a><br />" % (BASE_URL, group_name, BASE_URL, group_name)
							message += "To manage your squads, subscribe, or unsubscribe, visit <a href='http://%s/groups'>http://%s/my_groups</a><br />" % (BASE_URL, BASE_URL)
		
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
		membergroups_pending = MemberGroupPending.objects.filter(group=group).select_related()
		
		res['status'] = True
		res['group_name'] = group_name
		res['active'] = group.active
		res['public'] = group.public
		res['allow_attachments'] = group.allow_attachments
		res['members'] = []
		res['members_pending'] = []
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
		for membergroup in membergroups_pending:
			member_info = {'id': membergroup.id,
						   'email': membergroup.member.email,
						   'group_name': group_name, 
						   'admin': False,
						   'member': True,
						   'moderator': False,
						   'active': membergroup.member.is_active}
			res['members_pending'].append(member_info)

	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']	
	except:
		res['code'] = msg_code['UNKNOWN_ERROR']
	logging.debug(res)
	return res

def format_date_time(d):
	return datetime.datetime.strftime(d, '%Y/%m/%d %H:%M:%S')


def list_posts_page(threads, group, res, user=None, format_datetime=True, return_replies=True, text_limit=None):
	res['threads'] = []
	for t in threads:
		following = False
		muting = False
		
		if user:
			u = UserProfile.objects.get(email=user)
			following = Following.objects.filter(thread=t, user=u).exists()
			muting = Mute.objects.filter(thread=t, user=u).exists()
			
			member_group = MemberGroup.objects.filter(member=u, group=group)
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
			attachments = []
			for attachment in Attachment.objects.filter(msg_id=p.msg_id):
				url = "attachment/" + attachment.hash_filename
				attachments.append((attachment.true_filename, url))
			
			text = clean(p.post, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, styles=ALLOWED_STYLES)
			if text_limit:
				text = text[:text_limit]
			
			post_dict = {'id': p.id,
						'msg_id': p.msg_id, 
						'thread_id': p.thread_id, 
						'from': p.author.email if p.author else p.poster_email,
						'to': p.group.name, 
						'subject': escape(p.subject),
						'likes': post_likes, 
						'liked': user_liked,
						'text': text, 
						'timestamp': format_date_time(p.timestamp) if format_datetime else p.timestamp,
						'attachments': attachments
						}
			if p.forwarding_list:
				post_dict['forwarding_list'] = p.forwarding_list.email
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
		
		list_posts_page(threads, g, res, user=user, format_datetime=format_datetime, return_replies=return_replies)
			
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
		attachments = []
		for attachment in Attachment.objects.filter(msg_id=p.msg_id):
			url = "attachment/" + attachment.hash_filename
			attachments.append((attachment.true_filename, url))
		post_dict = {
					'id': str(p.id),
					'msg_id': p.msg_id, 
					'thread_id': p.thread_id, 
					'from': p.author.email if p.author else p.poster_email,
					'likes': post_likes,
					'to': p.group.name,
					'liked': user_liked,
					'subject': escape(p.subject), 
					'text': clean(p.post, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, styles=ALLOWED_STYLES), 
					'timestamp': p.timestamp,
					'attachments': attachments
					}
		if p.forwarding_list:
			post_dict['forwarding_list'] = p.forwarding_list.email
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
		attachments = []
		for attachment in Attachment.objects.filter(msg_id=p.msg_id):
			url = "attachment/" + attachment.hash_filename
			attachments.append((attachment.true_filename, url))
		res['status'] = True
		res['msg_id'] = p.msg_id
		res['thread_id'] = p.thread_id
		res['from'] = p.email
		res['tags'] = json.dumps(tags)
		res['subject'] = escape(p.subject)
		res['text'] = clean(p.post, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, styles=ALLOWED_STYLES)
		res['to'] = p.group.name
		res['attachments'] = attachments
		if p.forwarding_list:
			res['forwarding_list'] = p.forwarding_list.email
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

def _create_post(group, subject, message_text, user, sender_addr, msg_id, attachments=None, forwarding_list=None, post_status=None):

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

	if post_status == None:
		post_status = 'A'
	
	res = upload_attachments(attachments, msg_id)

	p = Post(msg_id=msg_id, author=user, poster_email = sender_addr, forwarding_list = forwarding_list, 
			subject=stripped_subj, post=message_text, group=group, thread=thread, status=post_status)
	p.save()
	
	if WEBSITE == 'murmur':
		for match in re.findall(r"[^[]*\[([^]]*)\]", subject):
			if match.lower() != group.name:
				_create_tag(group, thread, match)
		
		tags = list(extract_hash_tags(message_text))
		for tag in tags:
			if tag.lower() != group.name:
				_create_tag(group, thread, tag)
		
		tag_objs = Tag.objects.filter(tagthread__thread=thread)
		tags = list(tag_objs.values('name', 'color'))
		
		group_members = MemberGroup.objects.filter(group=group)
		
		recipients = []
		for m in group_members:
			if not m.no_emails and m.member.email != sender_addr:
				mute_tag = MuteTag.objects.filter(tag__in=tag_objs, group=group, user=m.member).exists()
				if not mute_tag:
					recipients.append(m.member.email)
			else:
				follow_tag = FollowTag.objects.filter(tag__in=tag_objs, group=group, user=m.member).exists()
				if follow_tag:
					recipients.append(m.member.email)
		
		if user:
			recipients.append(user.email)
			f = Following(user=user, thread=thread)
			f.save()

	elif WEBSITE == 'squadbox':
		# later on there will be various user options for this. for now just choose 
		# to send to all moderators.
		recipients = [m.member.email for m in MemberGroup.objects.filter(group=group, moderator=True)]
		tags = None
		tag_objs = None 
	
	return p, thread, recipients, tags, tag_objs

def insert_post_web(group_name, subject, message_text, user):
	res = {'status':False}
	thread = None
	
	try:
		group = Group.objects.get(name=group_name)
		user_member = MemberGroup.objects.filter(group=group, member=user)
		if user_member.exists():
			msg_id = base64.b64encode(user.email + str(datetime.datetime.now())).lower() + '@' + BASE_URL
			p, thread, recipients, tags, tag_objs = _create_post(group, subject, message_text, user, user.email, msg_id)
			res['status'] = True
			
			res['member_group'] = {'no_emails': user_member[0].no_emails,
								   'always_follow_thread': user_member[0].always_follow_thread}
	
			post_info = {'msg_id': p.msg_id,
						 'thread_id': thread.id,
						 'from': user.email,
						 'to': group_name,
						 'likes': 0,
						 'liked': False,
						 'subject': escape(p.subject),
						 'text': clean(p.post, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, styles=ALLOWED_STYLES), 
						 'timestamp': format_date_time(p.timestamp),
						}
			
			res['threads'] = []
			res['threads'].append({'thread_id': thread.id,
								   'post': post_info,
								   'num_replies': 0,
								   'replies': [],
								   'likes': 0,
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


def insert_post(group_name, subject, message_text, user, sender_addr, msg_id, attachments=None, forwarding_list=None, post_status=None):
	res = {'status':False}
	thread = None
	try:
		group = Group.objects.get(name=group_name)

		if WEBSITE == 'murmur':
			# this post did not come from a forwarding list. thus we should only
			# post it if the user is a member of the group. 
			if user and not forwarding_list:
				user_member = MemberGroup.objects.filter(group=group, member=user)
				if not user_member.exists():
					res['code'] = msg_code['NOT_MEMBER']
					return res

		# if we make it to here, then post is valid under one of following conditions:
		# 1) it's a normal post by a group member to the group.
		# 2) it's a post by a Murmur user, but it's being posted to this group via a list that fwds to this group. 
		# 3) it's a post by someone who doesn't use Murmur, via a list that fwds to this group. 
		# 4) it's a Squadbox post, so we don't care if the sender has an account / is authorized. 
		# _create_post will check which of user and forwarding list are None and post appropriately. 

		p, thread, recipients, tags, tag_objs = _create_post(group, subject, message_text, user, sender_addr, msg_id, attachments, forwarding_list=forwarding_list, post_status=post_status)
		res['status'] = True
		res['post_id'] = p.id
		res['msg_id'] = p.msg_id
		res['thread_id'] = thread.id
		res['tags'] = tags
		res['tag_objs'] = tag_objs
		res['recipients'] = recipients


	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']

	except Exception, e:
		logging.debug(e)
		if(thread and thread.id):
			thread.delete()
		res['code'] = msg_code['UNKNOWN_ERROR']

	logging.debug(res)
	return res


def insert_reply(group_name, subject, message_text, user, sender_addr, msg_id, forwarding_list=None, thread_id=None):
	res = {'status':False}
	try:
		group = Group.objects.get(name=group_name)
		group_members = UserProfile.objects.filter(membergroup__group=group)
		
		if user in group_members or forwarding_list:
			
			orig_post_subj = subject[4:].strip()
			
			post = Post.objects.filter((Q(subject=orig_post_subj) | Q(subject=subject)) & Q(group=group)).order_by('-timestamp')
			if post.count() >= 1:
				post = post[0]
			else:
				post = None
				
			if not thread_id:
				thread = Thread.objects.filter(subject=orig_post_subj, group=group).order_by('-timestamp')
			else:
				thread = Thread.objects.filter(id=thread_id)

			if thread.count() >= 1:
				thread = thread[0]
			else:
				thread = None
		
			if not thread:
				thread = Thread()
				thread.subject = orig_post_subj
				thread.group = group
				thread.save()
			
			tag_objs = Tag.objects.filter(tagthread__thread=thread)
			
			try:
				message_text = message_text.decode("utf-8")
			except Exception, e:
				logging.debug("guessing this is unicode then")
			
			message_text = message_text.encode("ascii", "ignore")
			
			r = Post(msg_id=msg_id, author=user, poster_email = sender_addr, forwarding_list = forwarding_list, 
				subject=subject, post = message_text, reply_to=post, group=group, thread=thread)
			r.save()
			
			thread.timestamp = datetime.datetime.now().replace(tzinfo=utc)
			thread.save()
			
			if not Following.objects.filter(user=user, thread=thread).exists(): 
				if user:
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
	p = Post.objects.get(id=int(post_id))
	membergroup = MemberGroup.objects.get(group=p.group, member=user)
	if membergroup:
		authormembergroup = MemberGroup.objects.get(group=p.group, member=p.author)
	if authormembergroup:
		if authormembergroup.upvote_emails:
			body = "Your post, \"" + p.subject + "\" in group [" + p.group.name + "] was upvoted by " + user.email + ".<br /><br /><hr /><br /> You can turn off these notifications in your <a href=\"http://" + BASE_URL + "/groups/" + p.group.name + "/edit_my_settings\">group settings</a>."
			mail = MailResponse(From = NO_REPLY, To = p.poster_email, Subject = '['+p.group.name+'] Your post was upvoted by '+user.email, Html = body)
			relay_mailer.deliver(mail, To = [p.poster_email])

	res = {'status':False}
	p = None
	try:
		p = Post.objects.get(id=int(post_id))
		if email:
			user = UserProfile.objects.get(email=email)
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

# add a new entry to whitelist/blacklist table, or update existing one
# user is the user who is adding them(we need to make sure they are authorized,
# email is the address to be blacklisted/whitelsited)
def update_blacklist_whitelist(user, group_name, email, whitelist, blacklist):
	res = {'status' : False}

	# illegal to have both set to true
	if whitelist and blacklist:
		res['code'] = msg_code['REQUEST_ERROR']
		logging.debug("Both whitelist and blacklist cannot be true")
		logging.debug(res)
		return res

	try:
		g = Group.objects.get(name=group_name)
		mg = MemberGroup.objects.get(Q(member=user, group=g), Q(admin=True) | Q(moderator=True))
		current = WhiteOrBlacklist.objects.filter(group=g, email=email)
		if current.exists():
			entry = current[0]
			entry.whitelist = whitelist
			entry.blacklist = blacklist
		else:
			entry = WhiteOrBlacklist(group=g, email=email, whitelist=whitelist, blacklist=blacklist)
		
		entry.save()
		res['status'] = True
		res['group_name'] = group_name
		res['email'] = email
		res['email_whitelisted'] = whitelist
		res['email_blacklisted'] = blacklist

	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']

	# they are not in the group or are not an admin of the group
	# later on should give people the option to also have mods add to list. 
	except MemberGroup.DoesNotExist:
		res['code'] = msg_code['PRIVILEGE_ERROR']

	except Exception, e:
		print e
		res['code'] = msg_code['UNKNOWN_ERROR']

	logging.debug(res)
	return res 

def update_post_status(user, group_name, post_id, new_status):
	res = {'status' : False}

	try:
		p = Post.objects.get(id=post_id)
		g = Group.objects.get(name=group_name)
		# only admins or moderators of a group can change post statuses
		mg = MemberGroup.objects.get(Q(admin=True) | Q(moderator=True), member=user, group=g)

		if new_status not in ALLOWED_MESSAGE_STATUSES:
			res['code'] = msg_code['INVALID_STATUS_ERROR'] % new_status
		else:
			p.status = new_status
			p.save()
			res['status'] = True
			res['post_id'] = post_id
			res['new_status'] = new_status

	except Post.DoesNotExist:
		res['code'] = msg_code['POST_NOT_FOUND_ERROR']

	except Group.DoesNotExist:
		res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']

	except MemberGroup.DoesNotExist:
		res['code'] = msg_code['PRIVILEGE_ERROR']

	except Exception, e:
		print e
		res['code'] = msg_code['UNKNOWN_ERROR']

	logging.debug(res)
	return res 

def load_pending_posts(user):
	res = {'status' : False}
	try:
		groups = Group.objects.filter(membergroup__member=user, membergroup__moderator=True)
		posts = Post.objects.filter(group__in=groups, status='P')
		posts_fixed = []
		for p in posts:
			post_dict = {'id': p.id,
						'msg_id': p.msg_id, 
						'from': p.author.email if p.author else p.poster_email,
						'to': p.group.name, 
						'subject': escape(p.subject),
						'text': p.post,
						'thread_id' : p.thread.id, 
						'timestamp': p.timestamp,
						}
			posts_fixed.append(post_dict)
		res['status'] = True
		res['posts'] = posts_fixed

	except Exception, e:
		logging.debug(e)
		res['status'] = False
		res['code'] = msg_code['UNKNOWN_ERROR']
		res['error'] = e

	return res
