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
from datetime import datetime, timedelta
import pytz
import django.db

'''
Murmur Mail Interface Handler

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''

@route("(address)@(host)", address="all", host=HOST)
@stateless
def all(message, address=None, host=None):
	# no public groups to list on squadbox. 
	if WEBSITE == 'squadbox':
		logging.debug("Ignored message to all@%s, no public groups to list" % HOST)
		return

	elif WEBSITE == 'murmur':
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
	# at least for now, for now we don't need this
	if WEBSITE == 'squadbox':
		logging.debug("Ignored message to create group via email, not used in Squadbox")
		return

	elif WEBSITE == 'murmur':
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

	if WEBSITE == 'squadbox':
		logging.debug("Ignoring activation message in squadbox")
		return

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

	if WEBSITE == 'squadbox':
		logging.debug("Ignoring deactivation message in squadbox")
		return

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


# A route to provide a contact email address for a group's administrator(s)
@route("(group_name)\\+admins@(host)", group_name=".+", host=HOST)
@stateless
def admins(message, group_name=None, host=None):

	# the only admin of a squadbox group is the person who
	# created the group. having the +admins route would just be 
	# a way to circumvent moderation / serves no purpose as of now
	if WEBSITE == 'squadbox':
		logging.debug("Ignoring message to admin")
		return

	elif WEBSITE == 'murmur':
		group_name = group_name.lower()
		name, sender_addr = parseaddr(message['From'].lower())

		try:
			group = Group.objects.get(name=group_name)

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

			admins = MemberGroup.objects.filter(group=group, admin=True)

			logging.debug(admins)

			for a in admins:
				email = a.member.email
				relay.deliver(mail, To = email)

		except Exception, e:
			logging.debug(e)
			send_error_email(group_name, e, sender_addr, ADMIN_EMAILS)	
			return


@route("(group_name)\\+subscribe@(host)", group_name=".+", host=HOST)
@stateless
def subscribe(message, group_name=None, host=None):

	# people will never be able to subscribe to a squadbox
	# group themselves; they must be added by the admin. 
	if WEBSITE == 'squadbox':
		logging.debug("No subscribing via email in Squadbox")
		return

	elif WEBSITE == 'murmur':
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

	if WEBSITE == 'squadbox':
		logging.debug("No unsubscribing via email in Squadbox")
		return

	elif WEBSITE == 'murmur':
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

	# for now I'm not sure what we would have here, 
	# but we can change this later on.
	if WEBSITE == 'squadbox':
		logging.debug("No group info sent via email in Squadbox")
		return

	elif WEBSITE == 'murmur':
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

def handle_post_murmur(message, group, host):

	_, list_addr = parseaddr(message['List-Id'])
	msg_id = message['Message-ID']
	email_message = message_from_string(str(message))
	to_header = email_message.get_all('to', [])

	# returns tuples of form (realname, address); only need second 
	to_emails = [i[1] for i in getaddresses(to_header)]

	msg_text = get_body(email_message)
	_, sender_addr = parseaddr(message['From'].lower())
	attachments = get_attachments(email_message)

	try:
		
		# try to detect and prevent duplicate posts 

		# check if we already got a post to this group with the same message_id
		existing_post_matching_id = Post.objects.filter(msg_id=msg_id, group=group)
		if existing_post_matching_id.exists():
			logging.debug("Already received post with same msg-id to this group")
			return

		ten_minutes_ago = datetime.now(pytz.utc) + timedelta(minutes=-10)
		existing_post_recent = Post.objects.filter(poster_email=sender_addr, group=group, 
										subject=message['Subject'], timestamp__gte = ten_minutes_ago)
		if existing_post_recent.exists():
			logging.debug("Post with same sender and subject sent to this group < 10 min ago")
			return

		# this is the case where we forward a message to a google group, and it forwards back to us
		if 'X-Original-Sender' in message and message['X-Original-Sender'].split('@')[0] == group.name:
			logging.debug('This message originally came from this list; not reposting')
			return

		message_is_reply = (message['Subject'][0:4].lower() == "re: ")
		
		if not message_is_reply:
			orig_message = message['Subject'].strip()
		else:
			orig_message = re.sub("\[.*?\]", "", message['Subject'][4:]).strip()
			if 'html' in msg_text:
				msg_text['html'] = remove_html_ps(msg_text['html'])
			if 'plain' in msg_text:
				msg_text['plain'] = remove_plain_ps(msg_text['plain'])
				
		if 'html' not in msg_text or msg_text['html'] == '':
			msg_text['html'] = markdown(msg_text['plain'])
		if 'plain' not in msg_text or msg_text['plain'] == '':
			msg_text['plain'] = html2text(msg_text['html'])

		if msg_text['plain'].startswith('unsubscribe\n') or msg_text['plain'] == 'unsubscribe':
			unsubscribe(message, group_name = group.name, host = HOST)
			return
		elif msg_text['plain'].startswith('subscribe\n') or msg_text['plain'] == 'subscribe':
			subscribe(message, group_name = group.name, host = HOST)
			return
		
		# try looking up sender in Murmur users
		user_lookup = UserProfile.objects.filter(email=sender_addr)

		# try using List-Id field from email
		original_list_lookup = ForwardingList.objects.filter(email=list_addr, group=group, can_post=True)

		# if no valid List-Id, try email's To field
		if not original_list_lookup.exists():
			original_list_lookup = ForwardingList.objects.filter(email__in=to_emails, group=group, can_post=True)

		# neither user nor fwding list exist so post is invalid - reject email
		if not user_lookup.exists() and not original_list_lookup.exists():
			error_msg = 'Your email is not in the Murmur system. Ask the admin of the group to add you.'
			send_error_email(group.name, error_msg, sender_addr, ADMIN_EMAILS)
			return

		# get user and/or forwarding list objects to pass to insert_reply or insert_post 
		user = None
		if user_lookup.exists():
			user = user_lookup[0]

		original_list = None
		original_list_email = None
		if original_list_lookup.exists():
			original_list = original_list_lookup[0]
			original_list_email = original_list.email

		if message_is_reply:
			res = insert_reply(group.name, "Re: " + orig_message, msg_text['html'], user, sender_addr, msg_id, forwarding_list=original_list)
		else:
			res = insert_post(group.name, orig_message, msg_text['html'], user, sender_addr, msg_id, attachments, forwarding_list=original_list)
			
		if not res['status']:
			send_error_email(group.name, res['code'], sender_addr, ADMIN_EMAILS)
			return

		subject = get_subject(message, res, group.name)
			
		mail = setup_post(message['From'],
							subject,	
							group.name)
			
		if 'references' in message:
			mail['References'] = message['references']
		elif 'message-id' in message:
			mail['References'] = message['message-id']	
	
		if 'in-reply-to' not in message:
			mail["In-Reply-To"] = message['message-id']
	
		msg_id = res['msg_id']
		mail['message-id'] = msg_id
		to_send =  res['recipients']
		
		ccs = email_message.get_all('cc', None)
		if ccs:
			mail['Cc'] = ','.join(ccs)

		logging.debug('TO LIST: ' + str(to_send))
		
		g = group
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
					if recip.email == sender_addr or recip.email in direct_recips:
						continue

					membergroup = membergroups.filter(member=recip)[0]
					following = followings.filter(user=recip).exists()
					muting = mutings.filter(user=recip).exists()
					tag_following = tag_followings.filter(user=recip)
					tag_muting = tag_mutings.filter(user=recip)

					if membergroup.receive_attachments:
						for attachment in attachments.get("attachments"):
							mail.attach(filename=attachment['filename'],
										content_type=attachment['mime'],
										data=attachment['content'],
										disposition=attachment['disposition'],
										id=attachment['id'])
				
					html_ps_blurb = html_ps(g, t, res['post_id'], membergroup, following, muting, tag_following, tag_muting, res['tag_objs'], original_list_email=original_list_email)
					html_ps_blurb = unicode(html_ps_blurb)
					mail.Html = get_new_body(msg_text, html_ps_blurb, 'html')
					
					plain_ps_blurb = plain_ps(g, t, res['post_id'], membergroup, following, muting, tag_following, tag_muting, res['tag_objs'], original_list_email=original_list_email)
					mail.Body = get_new_body(msg_text, plain_ps_blurb, 'plain')
		
					relay.deliver(mail, To = recip.email)

			fwd_to_lists = ForwardingList.objects.filter(group=g, can_receive=True)

			for l in fwd_to_lists:
				# non murmur list, send as usual 
				if HOST not in l.email:

					footer_html = html_forwarded_blurb(g.name, l.email, original_list_email=original_list_email)
					footer_plain = plain_forwarded_blurb(g.name, l.email, original_list_email=original_list_email)

					mail.Html = get_new_body(msg_text, footer_html, 'html')
					mail.Body = get_new_body(msg_text, footer_plain, 'plain')

					relay.deliver(mail, To = l.email)
				# it's another murmur list. can't send mail to ourself ("loops back to 
				#myself" error) so have to directly pass back to handle_post 
				else:
					group_name = l.email.split('@')[0]
					handle_post(message, address=group_name)


		except Exception, e:
			logging.debug(e)
			send_error_email(group.name, e, None, ADMIN_EMAILS)
			
			# try to deliver mail even without footers
			mail.Html = msg_text['html']
			mail.Body = msg_text['plain']
			relay.deliver(mail, To = to_send)
				
	except Exception, e:
		logging.debug(e)
		send_error_email(group.name, e, None, ADMIN_EMAILS)
		return
		
def handle_post_squadbox(message, group, host):

	msg_id = message['Message-ID']
	email_message = message_from_string(str(message))
	msg_text = get_body(email_message)
	_, sender_addr = parseaddr(message['From'].lower())
	subj = message['Subject'].strip()

	if 'html' not in msg_text or msg_text['html'] == '':
		msg_text['html'] = markdown(msg_text['plain'])
	if 'plain' not in msg_text or msg_text['plain'] == '':
		msg_text['plain'] = html2text(msg_text['html'])

	attachments = get_attachments(email_message)

	# initially, assume that it's pending and will go through moderation. 
	status = 'P'

	# if whitelisted, accept; if blacklisted, reject 
	white_or_blacklist = WhiteOrBlacklist.objects.filter(group=group, email=sender_addr)
	if white_or_blacklist.exists():
		w_or_b = white_or_blacklist[0]
		if w_or_b.blacklist:
			status = 'R' # if blacklist could means "gets moderated", need to change. 
		elif w_or_b.whitelist:
			status = 'A' # sender is whitelisted, so we can accept the mesasge 

	# either:
	# 1) sender is whitelisted
	# 2) sender is blacklisted, but the user still wants rejected messages. 
	if status == 'A' or (status == 'R' and group.send_rejected_tagged):
		# we can just send it on to the intended recipient, i.e. the admin of the group. 
		mg = MemberGroup.objects.get(group=group, admin=True)
		admin = mg.member

		new_subj = subj
		if status == 'R':
			new_subj = '[Rejected] ' + new_subj 

		mail = MurmurMailResponse(From = message['From'], To = admin.email, Subject = new_subj)

		if 'references' in message:
			mail['References'] = message['references']
		elif 'message-id' in message:
			mail['References'] = message['message-id']	
	
		if 'in-reply-to' not in message:
			mail["In-Reply-To"] = message['message-id']

		mail['message-id'] = msg_id
		ccs = email_message.get_all('cc', None)
		if ccs:
			mail['Cc'] = ','.join(ccs)

		for attachment in attachments.get("attachments"):
			mail.attach(filename=attachment['filename'],
						content_type=attachment['mime'],
						data=attachment['content'],
						disposition=attachment['disposition'],
						id=attachment['id'])

		if status == 'A':
			reason = 'whitelist'
		elif status == 'R':
			reason = 'blacklist'

		html_blurb = unicode(html_ps_squadbox(group.name, sender_addr, reason))
		mail.Html = get_new_body(msg_text, html_blurb, 'html')

		plain_blurb = plain_ps_squadbox(group.name, sender_addr, reason)
		mail.Body = get_new_body(msg_text, plain_blurb, 'plain')

		relay.deliver(mail, To = admin.email)

	# send notification to mods (probably should change to not do this every time)
	elif status == 'P':

		moderators = MemberGroup.objects.filter(group=group, moderator=True)

		if len(moderators) == 0:
			error_msg = 'Error: the group %s has no moderators' % group.name
			logging.debug(error_msg)
			send_error_email(group.name, error_msg, None, ADMIN_EMAILS)
			# maybe here we should just send the original email on to the admin here then? 
			return

		outgoing_msg = setup_moderation_post(group.name)
		outgoing_msg['message-id'] = base64.b64encode(group.name + str(datetime.now())).lower() + '@' + BASE_URL

		for m in moderators:
			member = m.member
			relay.deliver(outgoing_msg, To=member.email)
			logging.debug("sending msg to moderator %s" % member.email)
	
	# if pending or rejected, we need to put it in the DB 
	if status == 'P' or status == 'R':
		res = insert_post(group.name, subj, msg_text['html'], None, sender_addr, msg_id, forwarding_list=None, post_status=status)
		if not res['status']:
			send_error_email(group.name, res['code'], None, ADMIN_EMAILS)
			return

@route("(address)@(host)", address=".+", host=HOST)
@stateless
def handle_post(message, address=None, host=None):
	
	# restart the db connection
	django.db.close_connection()
	
	if '+' in address and '__' in address:
		return

	address = address.lower()

	reserved = filter(lambda x: address.endswith(x), RESERVED)
	if(reserved):
		return
	
	_, sender_addr = parseaddr(message['From'].lower())
	group_name = address
	try:
		group = Group.objects.get(name=group_name)
	except Exception, e:
		logging.debug(e)
		send_error_email(group_name, e, sender_addr, ADMIN_EMAILS)	
		return

	email_message = message_from_string(str(message))

	attachments = get_attachments(email_message)
	res = check_attachments(attachments, group.allow_attachments)
	if not res['status']:
		send_error_email(group_name, res['error'], sender_addr, ADMIN_EMAILS)
		return
	
	# deal with Gmail forwarding verification emails:
	if sender_addr == "forwarding-noreply@google.com":
		email_message = email.message_from_string(str(message))
		msg_text = get_body(email_message)['plain']
		forward_to = msg_text.split(' ', 1)[0]
		content = "The message below is forwarded to you from Gmail - to complete the setup of your Gmail integration, please click the confirmation link below.\n\n"
		mail = MailResponse(From = NO_REPLY, To = forward_to, Subject = (WEBSITE + " setup: please click the confirmation link inside"), Body = content + msg_text)
		relay.deliver(mail)
		return

	if WEBSITE == 'squadbox':
		handle_post_squadbox(message, group, host)

	elif WEBSITE == 'murmur':
		handle_post_murmur(message, group, host)


@route("(group_name)\\+(thread_id)(suffix)@(host)", group_name=".+", thread_id=".+", suffix=FOLLOW_SUFFIX+"|"+FOLLOW_SUFFIX.upper(), host=HOST)
@stateless
def handle_follow(message, group_name=None, thread_id=None, suffix=None, host=None):

	if WEBSITE == 'squadbox':
		return

	elif WEBSITE == 'murmur':
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

	if WEBSITE == 'squadbox':
		return

	elif WEBSITE == 'murmur':

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

	if WEBSITE == 'squadbox':
		return

	elif WEBSITE == 'murmur':
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

	if WEBSITE == 'squadbox':
		return

	elif WEBSITE == 'murmur':
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

	if WEBSITE == 'squadbox':
		return

	elif WEBSITE == 'murmur':
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

	if WEBSITE == 'squadbox':
		return

	elif WEBSITE == 'murmur':

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

	if WEBSITE == 'squadbox':
		return

	elif WEBSITE == 'murmur':

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

	if WEBSITE == 'squadbox':
		return

	elif WEBSITE == 'murmur':

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

	if WEBSITE == 'squadbox':
		return

	elif WEBSITE == 'murmur':

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

	if WEBSITE == 'squadbox':
		# we should change this to actually send a useful help email
		# with the possible via-email commands in squadbox
		return

	elif WEBSITE == 'murmur':
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

	subj_string = str(message['Subject']).lower()
	activation_str = ("account activation on %s" % WEBSITE).lower()
	reset_str = ("password reset on %s" % WEBSITE).lower()

	logging.debug(message['Subject'])
	logging.debug(message['To'])
	logging.debug(message['From'])

	if message['From'].encode('utf-8') == NO_REPLY and (activation_str in subj_string or reset_str in subj_string):
		
		email_message = email.message_from_string(str(message))
		msg_text = get_body(email_message)
		mail = MailResponse(From = NO_REPLY, To = message['To'], Subject = message['Subject'], Body = msg_text['plain'])
		relay.deliver(mail)
