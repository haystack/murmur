import logging, time, base64
from lamson.routing import route, stateless
from config.settings import relay
from http_handler.settings import WEBSITE
from schema.models import *
from lamson.mail import MailResponse
from email.utils import *
from email import message_from_string
from engine.main import *
from utils import *
from html2text import html2text
from markdown2 import markdown
from django.db.utils import OperationalError
import django.db

'''
Murmur Mail Interface Handler

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''


@route("(address)@(host)", address="all", host=HOST)
@stateless
def all(message, address=None, host=None):
	res = list_groups()
	subject = "Listing Groups -- Success"
	body = "Listing all the groups \n\n"
	if(res['status']):
		for g in res['groups']:
			body= body + "Name: " + g['name'] + "\t\tActive:" + str(g['active']) + "\n"  
	else:
		subject = "Listing Groups -- Error"
		body = "Error Message: %s" %(res['code'])
	mail = MailResponse(From = NO_REPLY, To = message['From'], Subject = subject, Body = body)
	relay.deliver(mail)


@route("(group_name)\\+create@(host)", group_name=".+", host=HOST)
@stateless
def create(message, group_name=None, host=None):
	group_name = group_name.lower()
	name, addr = parseaddr(message['from'].lower())
	res = create_group(group_name, addr)
	subject = "Create Group -- Success"
	body = "Mailing group %s@%s created" %(group_name, host)
	if(not res['status']):
		subject = "Create Group -- Error"
		body = "Error Message: %s" %(res['code'])
	mail = MailResponse(From = NO_REPLY, To = message['From'], Subject = subject, Body = body)
	relay.deliver(mail)

@route("(group_name)\\+activate@(host)", group_name=".+", host=HOST)
@stateless
def activate(message, group_name=None, host=None):
	group = None
	group_name = group_name.lower()
	name, addr = parseaddr(message['from'].lower())
	res = activate_group(group_name, addr)
	subject = "Activate Group -- Success"
	body = "Activated: %s@%s" %(group_name, host)
	if(not res['status']):
		subject = "Activate Group -- Error"
		body = "Error Message: %s" %(res['code'])
	mail = MailResponse(From = NO_REPLY, To = message['From'], Subject = subject, Body = body) 
	relay.deliver(mail)




@route("(group_name)\\+deactivate@(host)", group_name=".+", host=HOST)
@stateless
def deactivate(message, group_name=None, host=None):
	group = None
	group_name = group_name.lower()
	name, addr = parseaddr(message['from'].lower())
	res = deactivate_group(group_name, addr)
	subject = "De-activate Group -- Success"
	body = "De-activated: %s@%s" %(group_name, host)
	if(not res['status']):
		subject = "De-activate Group -- Error"
		body = "Error Message: %s" %(res['code'])
	mail = MailResponse(From = NO_REPLY, To = message['From'], Subject = subject, Body = body) 
	relay.deliver(mail)


@route("(group_name)\\+admins@(host)", group_name=".+", host=HOST)
@stateless
def admins(message, group_name=None, host=None):

	group_name = group_name.lower()
	name, sender_addr = parseaddr(message['From'].lower())

	try:
		group = Group.objects.get(name=group_name)
	except Exception, e:
		logging.debug(e)
		send_error_email(group_name, e, sender_addr, ADMIN_EMAILS)	
		return

	email_message = message_from_string(str(message))
	msg_text = get_body(email_message)

	if 'html' not in msg_text or msg_text['html'] == '':
		msg_text['html'] = markdown(msg_text['plain'])
	if 'plain' not in msg_text or msg_text['plain'] == '':
		msg_text['plain'] = html2text(msg_text['html'])

	mail = MurmurMailResponse(From = sender_addr, 
			To = group_name+"+admins@" + HOST, 
			Subject = message['Subject'])

	mail.Html = msg_text['html']
	mail.Body = msg_text['plain']

	mail.Body += '\n\nYou are receiving this message because you are an admin of the Murmur group %s.' %(group_name)
	mail.Html += '<BR><BR>You are receiving this message because you are an admin of the Murmur group %s.' %(group_name)

	try:
		admins = MemberGroup.objects.filter(group=group, admin=True)
	except Exception, e:
		logging.debug(e)
		send_error_email(group_name, e, sender_addr, ADMIN_EMAILS)	
		return

	logging.debug(admins)
	for a in admins:
		email = a.member.email
		relay.deliver(mail, To = email)


@route("(group_name)\\+subscribe@(host)", group_name=".+", host=HOST)
@stateless
def subscribe(message, group_name=None, host=None):

	group = None
	group_name = group_name.lower()
	name, addr = parseaddr(message['from'].lower())

	try:
		user = UserProfile.objects.get(email=addr)
		group = Group.objects.get(name=group_name)

	except UserProfile.DoesNotExist:
		error_msg = 'Your email is not in the %s system. Ask the admin of the group to add you.' % WEBSITE
		send_error_email(group_name, error_msg, addr, ADMIN_EMAILS)
		return

	except Group.DoesNotExist:
		error_msg = 'The group' + group_name + 'does not exist.'
		send_error_email(group_name, error_msg, addr, ADMIN_EMAILS)
		return

	if not group.public:
		error_msg = 'The group ' + group_name + ' is private. Ask the admin of the group to add you.'
		send_error_email(group_name, error_msg, addr, ADMIN_EMAILS)
		return

	res = subscribe_group(group_name, user)
	subject = "Subscribe -- Success"
	body = "You are now subscribed to: %s@%s" %(group_name, host)

	if(not res['status']):
		subject = "Subscribe -- Error"
		body = "Error Message: %s" %(res['code'])

	mail = MailResponse(From = NO_REPLY, To = message['From'], Subject = subject, Body = body) 
	relay.deliver(mail)




@route("(group_name)\\+unsubscribe@(host)", group_name=".+", host=HOST)
@stateless
def unsubscribe(message, group_name=None, host=None):

	group = None
	group_name = group_name.lower()
	name, addr = parseaddr(message['from'].lower())

	try:
		user = UserProfile.objects.get(email=addr)

	except UserProfile.DoesNotExist:
		error_msg = 'Your email is not in the %s system. Ask the admin of the group to add you.' % WEBSITE
		send_error_email(group_name, error_msg, addr, ADMIN_EMAILS)
		return

	res = unsubscribe_group(group_name, user)
	subject = "Unsubscribe -- Success"
	body = "You are now unsubscribed from: %s@%s." %(group_name, host)
	body += " To resubscribe, reply to this email."

	if(not res['status']):
		subject = "Unsubscribe -- Error"
		body = "Error Message: %s" %(res['code'])

	mail = MailResponse(From = NO_REPLY, To = message['From'], Subject = subject, Body = body)
	mail['Reply-To'] = '%s+subscribe@%s' %(group_name, host)
	relay.deliver(mail)




@route("(group_name)\\+info@(host)", group_name=".+", host=HOST)
@stateless
def info(message, group_name=None, host=None):
	group_name = group_name.lower()
	res = group_info(group_name)
	subject = "Group Info -- Success"
	body = "Group info for %s:\n" %(group_name)
	if(res['status']):
		body = "Group Name: %s@%s, Active: %s\n\n" %(res['group_name'], host, res['active'])
		for member in res['members']:			
			body += "%s : %s\n" %('Email: ', member['email'])
			body += "%s : %s\n" %('Active: ', member['active'])
			body += "%s : %s\n" %('Member: ', member['member'])
			body += "%s : %s\n" %('Guest: ', member['guest'])
			body += "%s : %s\n" %('Moderator: ', member['moderator'])
			body += "%s : %s\n" %('Admin: ', member['admin'])
		body += "\n..........................\n"       
	else:
		subject = "Group Info -- Error"
		body = "Error Message: %s" %(res['code'])
		
	mail = MailResponse(From = NO_REPLY, To = message['From'], Subject = subject, Body = body)
	relay.deliver(mail)


@route("(address)@(host)", address=".+", host=HOST)
@stateless
def handle_post(message, address=None, host=None):
	if '+' in address and '__' in address:
		return

	try:
		#does this fix the MySQL has gone away error?
		django.db.close_connection()
		
		address = address.lower()
		name, user_addr = parseaddr(message['From'].lower())
		reserved = filter(lambda x: address.endswith(x), RESERVED)
		if(reserved):
			return
		
		group_name = address
		try:
			group = Group.objects.get(name=group_name)
		except Exception, e:
			logging.debug(e)
			send_error_email(group_name, e, user_addr, ADMIN_EMAILS)	
			return

		message_is_reply = (message['Subject'][0:4].lower() == "re: ")
		
		if not message_is_reply:
			orig_message = message['Subject'].strip()
		else:
			orig_message = re.sub("\[.*?\]", "", message['Subject'][4:]).strip()
		
		email_message = message_from_string(str(message))
		msg_text = get_body(email_message)
	
		attachments = get_attachments(email_message)
		res = check_attachments(attachments, group.allow_attachments)

		if not res['status']:
			send_error_email(group_name, res['error'], user_addr, ADMIN_EMAILS)
			return
	
		if message_is_reply:
			if 'html' in msg_text:
				msg_text['html'] = remove_html_ps(msg_text['html'])
			if 'plain' in msg_text:
				msg_text['plain'] = remove_plain_ps(msg_text['plain'])
				
		if 'html' not in msg_text or msg_text['html'] == '':
			msg_text['html'] = markdown(msg_text['plain'])
		if 'plain' not in msg_text or msg_text['plain'] == '':
			msg_text['plain'] = html2text(msg_text['html'])

		if msg_text['plain'].startswith('unsubscribe\n') or msg_text['plain'] == 'unsubscribe':
			unsubscribe(message, group_name = group_name, host = HOST)
			return
		elif msg_text['plain'].startswith('subscribe\n') or msg_text['plain'] == 'subscribe':
			subscribe(message, group_name = group_name, host = HOST)
			return
		
		try:
			user = UserProfile.objects.get(email=user_addr)
		except UserProfile.DoesNotExist:
			error_msg = 'Your email is not in the %s system. Ask the admin of the group to add you.' % WEBSITE
			send_error_email(group_name, error_msg, user_addr, ADMIN_EMAILS)
			return

		if message_is_reply:
			res = insert_reply(group_name, "Re: " + orig_message, msg_text['html'], user)
		else:
			res = insert_post(group_name, orig_message, msg_text['html'], user)
			
		if not res['status']:
			send_error_email(group_name, res['code'], user_addr, ADMIN_EMAILS)
			return
	
		subject = get_subject(message, res, group_name)
			
		mail = setup_post(message['From'],
							subject,	
							group_name)
			
		for attachment in attachments.get("attachments"):
			mail.attach(filename=attachment['filename'],
						content_type=attachment['mime'],
						data=attachment['content'],
						disposition=attachment['disposition'],
						id=attachment['id'])
			
		if 'references' in message:
			mail['References'] = message['references']
		elif 'message-id' in message:
			mail['References'] = message['message-id']	
	
		if 'in-reply-to' not in message:
			mail["In-Reply-To"] = message['message-id']
	
		msg_id = res['msg_id']
		to_send =  res['recipients']
		
		mail['message-id'] = msg_id
		
		ccs = email_message.get_all('cc', None)
		if ccs:
			mail['Cc'] = ','.join(ccs)

		logging.debug('TO LIST: ' + str(to_send))
		
		g = Group.objects.get(name=group_name)
		t = Thread.objects.get(id=res['thread_id'])
		
		direct_recips = get_direct_recips(email_message)
		
		try:
			if len(to_send) > 0:
				
				recips = UserProfile.objects.filter(email__in=to_send)
				membergroups = MemberGroup.objects.filter(group=g, member__in=recips)
				followings = Following.objects.filter(thread=t, user__in=recips)
				mutings = Mute.objects.filter(thread=t, user__in=recips)
				
				tag_followings = FollowTag.objects.filter(group=g, tag__in=res['tag_objs'], user__in=recips)
				tag_mutings = MuteTag.objects.filter(group=g, tag__in=res['tag_objs'], user__in=recips)
				
				for recip in recips:
					
					# Don't send email to the sender if it came from email
					# Don't send email to people that already directly got the email via CC/BCC
					if recip.email == user_addr or recip.email in direct_recips:
						continue

					membergroup = membergroups.filter(member=recip)[0]
					following = followings.filter(user=recip).exists()
					muting = mutings.filter(user=recip).exists()
					tag_following = tag_followings.filter(user=recip)
					tag_muting = tag_mutings.filter(user=recip)
				
					html_ps_blurb = html_ps(g, t, res['post_id'], membergroup, following, muting, tag_following, tag_muting, res['tag_objs'])
					html_ps_blurb = unicode(html_ps_blurb)
					mail.Html = get_new_body(msg_text, html_ps_blurb, 'html')
					
					plain_ps_blurb = plain_ps(g, t, res['post_id'], membergroup, following, muting, tag_following, tag_muting, res['tag_objs'])
					mail.Body = get_new_body(msg_text, plain_ps_blurb, 'plain')
		
					relay.deliver(mail, To = recip.email)

		except Exception, e:
			logging.debug(e)
			send_error_email(group_name, e, None, ADMIN_EMAILS)
			
			# try to deliver mail even without footers
			mail.Html = msg_text['html']
			mail.Body = msg_text['plain']
			relay.deliver(mail, To = to_send)
				
	except Exception, e:
		logging.debug(e)
		send_error_email(group_name, e, None, ADMIN_EMAILS)
		return
		
		

@route("(group_name)\\+(thread_id)(suffix)@(host)", group_name=".+", thread_id=".+", suffix=FOLLOW_SUFFIX+"|"+FOLLOW_SUFFIX.upper(), host=HOST)
@stateless
def handle_follow(message, group_name=None, thread_id=None, suffix=None, host=None):
	_, addr = parseaddr(message['From'].lower())
	res = follow_thread(thread_id, email=addr)

	if res['status']:
		body = "Success! You are now following the thread \"%s\". You will receive emails for all following replies to this thread." % res['thread_name']
	else:
		body = "Sorry there was an error: %s" % res['code']

	mail = MailResponse(From = NO_REPLY, To = addr, Subject = res['thread_name'], Body = body)
	relay.deliver(mail)


@route("(group_name)\\+(thread_id)(suffix)@(host)", group_name=".+", thread_id=".+", suffix=UNFOLLOW_SUFFIX+"|"+UNFOLLOW_SUFFIX.upper(), host=HOST)
@stateless
def handle_unfollow(message, group_name=None, thread_id=None, suffix=None, host=None):
	_, addr = parseaddr(message['From'].lower())
	res = unfollow_thread(thread_id, email=addr)

	if res['status']:
		body = "You unfollowed the thread \"%s\" successfully." % res['thread_name']
	else:
		body =  "Error Message: %s" % res['code']

	mail = MailResponse(From = NO_REPLY, To = addr, Subject = res['thread_name'], Body = body)
	relay.deliver(mail)


@route("(group_name)\\+(thread_id)(suffix)@(host)", group_name=".+", thread_id=".+", suffix=MUTE_SUFFIX+"|"+MUTE_SUFFIX.upper(), host=HOST)
@stateless
def handle_mute(message, group_name=None, thread_id=None, suffix=None, host=None):

	_, addr = parseaddr(message['From'].lower())
	res = mute_thread(thread_id, email=addr)

	if(res['status']):
		body = "Success! You have now muted the thread \"%s\"." % res['thread_name']
	else:
		body = "Sorry there was an error: %s" % (res['code'])

	mail = MailResponse(From = NO_REPLY, To = addr, Subject = res['thread_name'], Body = body)
	relay.deliver(mail)


@route("(group_name)\\+(thread_id)(suffix)@(host)", group_name=".+", thread_id=".+", suffix=UNMUTE_SUFFIX+"|"+UNMUTE_SUFFIX.upper(), host=HOST)
@stateless
def handle_unmute(message, group_name=None, thread_id=None, suffix=None, host=None):

	_, addr = parseaddr(message['From'].lower())
	res = unmute_thread(thread_id, email=addr)

	if(res['status']):
		body = "You unmuted the thread \"%s\" successfully. You will receive emails for all following replies to this thread." % res['thread_name']
	else:
		body = "Error Message: %s" %(res['code'])
	
	mail = MailResponse(From = NO_REPLY, To = addr, Subject = res['thread_name'], Body = body)
	relay.deliver(mail)


@route("(group_name)\\+(tag_name)(suffix)@(host)", group_name=".+", tag_name=".+", suffix=FOLLOW_TAG_SUFFIX+"|"+FOLLOW_TAG_SUFFIX.upper(), host=HOST)
@stateless
def handle_follow_tag(message, group_name=None, tag_name=None, suffix=None, host=None):

	_, addr = parseaddr(message['From'].lower())
	res = follow_tag(tag_name, group_name, email=addr)

	if(res['status']):
		body = "Success! You are now following the tag \"%s\". You will receive emails for all following emails with this tag." % res['tag_name']
	else:
		body = "Sorry there was an error: %s" % (res['code'])

	mail = MailResponse(From = NO_REPLY, To = addr, Subject = res['tag_name'], Body = body)
	relay.deliver(mail)


@route("(group_name)\\+(tag_name)(suffix)@(host)", group_name=".+", tag_name=".+", suffix=UNFOLLOW_TAG_SUFFIX+"|"+UNFOLLOW_TAG_SUFFIX.upper(), host=HOST)
@stateless
def handle_unfollow_tag(message, group_name=None, tag_name=None, suffix=None, host=None):

	_, addr = parseaddr(message['From'].lower())
	res = unfollow_tag(tag_name, group_name, email=addr)

	if(res['status']):
		body = "You unfollowed the tag \"%s\" successfully." % res['tag_name']
	else:
		body = "Error Message: %s" %(res['code'])
	
	mail = MailResponse(From = NO_REPLY, To = addr, Subject = res['tag_name'], Body = body)
	relay.deliver(mail)


@route("(group_name)\\+(tag_name)(suffix)@(host)", group_name=".+", tag_name=".+", suffix=MUTE_TAG_SUFFIX+"|"+MUTE_TAG_SUFFIX.upper(), host=HOST)
@stateless
def handle_mute_tag(message, group_name=None, tag_name=None, suffix=None, host=None):
	_, addr = parseaddr(message['From'].lower())
	res = mute_tag(tag_name, group_name, email=addr)
	if(res['status']):
		body = "Success! You have now muted the tag \"%s\"." % res['tag_name']
	else:
		body = "Sorry there was an error: %s" % (res['code'])

	mail = MailResponse(From = NO_REPLY, To = addr, Subject = res['tag_name'], Body = body)
	relay.deliver(mail)

@route("(group_name)\\+(tag_name)(suffix)@(host)", group_name=".+", tag_name=".+", suffix=UNMUTE_TAG_SUFFIX+"|"+UNMUTE_TAG_SUFFIX.upper(), host=HOST)
@stateless
def handle_unmute_tag(message, group_name=None, tag_name=None, suffix=None, host=None):
	_, addr = parseaddr(message['From'].lower())
	res = unmute_tag(tag_name, group_name, email=addr)
	if(res['status']):
		body = "You unmuted the tag \"%s\" successfully. You will receive emails for all emails to this tag." % res['tag_name']
	else:
		body = "Error Message: %s" %(res['code'])
	
	mail = MailResponse(From = NO_REPLY, To = addr, Subject = res['tag_name'], Body = body)
	relay.deliver(mail)

@route("(group_name)\\+(post_id)(suffix)@(host)", group_name=".+", post_id=".+", suffix=UPVOTE_SUFFIX+"|"+UPVOTE_SUFFIX.upper(), host=HOST)
@stateless
def handle_upvote(message, group_name=None, post_id=None, suffix=None, host=None):
	name, addr = parseaddr(message['from'].lower())
	res = upvote(post_id, email=addr, user=None)
	if(res['status']):
		subject = 'Success'
		body = "Upvoted the post: %s" %(post_id)

	else:
		subject = 'Error'
		body = "Invalid post: %s" %(post_id)

	mail = MailResponse(From = NO_REPLY, To = addr, Subject = subject, Body = body)
	relay.deliver(mail)

@route("(address)@(host)", address="help", host=HOST)
@stateless
def help(message, address=None, host=None):
	to_addr = message['From']
	from_addr = address + '@' + HOST
	subject = "Help"
	body = "Welcome to %s. Please find below a general help on managing a group mailing list.\n\n" %(host)
	body += "To create a new group: <name>+create@%s\n" %(host)
	body += "To activate/re-activate your group: <name>+activate@%s\n" %(host)
	body += "To de-activate your group: <name>+deactivate@%s\n" %(host)
	body += "To subscribe to a group: <name>+subscribe@%s\n" %(host)
	body += "To unsubscribe from a group: <name>+unsubscribe@%s\n" %(host)
	body += "To see details of a group: <name>+info@%s\n" %(host)
	body += "To see a listing of all the groups: all@%s\n" %(host)
	body += "To get help: help@%s\n" %(host)
	body += "To post message to a group: <name>@%s\n\n" %(host)
	body += "Please substitute '<name>' with your group name." 	
	mail = MailResponse(From = from_addr, To = to_addr, Subject = subject, Body = body)
	relay.deliver(mail)
	return


@route("(address)@(host)", address=".+", host=".+")
@stateless
def send_account_info(message, address=None, host=None):
	logging.debug(message['Subject'])
	if str(message['From']) == "no-reply@" + HOST and ("Account activation on %s" % WEBSITE in str(message['Subject']) or "Password reset on %s" % WEBSITE in str(message['Subject'])):
		logging.debug(message['Subject'])
		logging.debug(message['To'])
		logging.debug(message['From'])
		
		email_message = email.message_from_string(str(message))
		msg_text = get_body(email_message)
		mail = MailResponse(From = NO_REPLY, To = message['To'], Subject = message['Subject'], Body = msg_text['plain'])
		relay.deliver(mail)
