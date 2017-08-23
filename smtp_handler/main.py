import logging, time, base64
from lamson.routing import route, stateless
from config.settings import relay
from http_handler.settings import WEBSITE
from schema.models import *
from lamson.mail import MailResponse
from email.utils import *
from email import message_from_string
from engine.main import *
from engine.s3_storage import upload_message
from utils import *
from django.db.utils import OperationalError
from datetime import datetime
import pytz
import django.db

'''
Murmur Mail Interface Handler

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''

GROUP_OR_SQUAD = {'murmur' : 'group', 'squadbox' : 'squad'}

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

			msg_text = check_html_and_plain(msg_text)

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

def handle_post_murmur(message, group, host, verified):

	# just setting up a bunch of variables with values we'll use
	email_message = message_from_string(str(message))

	to_header = email_message.get_all('to', [])
	to_emails = [i[1] for i in getaddresses(to_header)]
	sender_name, sender_addr = parseaddr(message['From'])
	sender_addr = sender_addr.lower()
	if not sender_name:
		sender_name = None

	# any of the lists in the "to" field might be what forwarded this to us
	possible_list_addresses = to_emails
	# if List-Id set that might also be it 
	_, list_addr = parseaddr(message['List-Id'])
	if list_addr:
		possible_list_addresses.append(list_addr)

	# according to rules and group membership, can this post go through?
	can_post = check_if_can_post_murmur(group, sender_addr, possible_list_addresses)
	if not can_post['can_post']:
		error_msg = 'You are not authorized to post to the Murmur group %s@%s. This is either ' % (group.name, host) + \
		'because you are posting directly to the group, but you are not a member, or because you are posting to ' + \
		'a mailing list that forwards to the Murmur group, but does not have permission to do so.'

		send_error_email(group.name, error_msg, sender_addr, ADMIN_EMAILS)
		return

	# if this looks like a double-post, ignore it
	if check_duplicate(message, group, sender_addr):
		logging.debug("ignoring duplicate")
		return

	msg_id = message['Message-ID']
	msg_text = get_body(email_message)
	message_is_reply = (message['Subject'][0:4].lower() == "re: ")
	msg_text = check_html_and_plain(msg_text, message_is_reply)

	if msg_text['plain'].startswith('unsubscribe\n') or msg_text['plain'] == 'unsubscribe':
		unsubscribe(message, group_name = group.name, host = HOST)
		return
	elif msg_text['plain'].startswith('subscribe\n') or msg_text['plain'] == 'subscribe':
		subscribe(message, group_name = group.name, host = HOST)
		return

	# get user and/or forwarding list objects (however we are receiving this message) 
	if can_post['reason'] == 'is_member':
		user = can_post['which_user']
		original_list = None
		original_list_email = None
	elif can_post['reason'] == 'via_list':
		user = None
		original_list = can_post['which_list']
		original_list_email = original_list.email

	# if we make it to here, then post is valid under one of following conditions:
	# 1) it's a normal post by a group member to the group.
	# 2) it's a post via a list that is allowed to fwd to this group, by someone who may
	# or may not be a Murmur user, but is not a group member. 

	# _create_post (called by both insert_reply and insert_post) will check which of user 
	# and forwarding list are None and post appropriately. 
	try:
		res = get_attachments(email_message)
		check = check_attachments(res, group.allow_attachments)

		if not check['status']:
			send_error_email(group.name, check['error'], sender_addr, ADMIN_EMAILS)
			return

		attachments = res['attachments']

		if message_is_reply:
			post_subject = "Re: " + re.sub("\[.*?\]", "", message['Subject'][4:]).strip()
			insert_func = insert_reply
		else:
			post_subject = message['Subject'].strip()
			insert_func = insert_post
			
		args = [group.name, post_subject, msg_text['html'], user, sender_addr, msg_id, verified]
		keyword_args = {'attachments' : attachments, 'forwarding_list' : original_list, 'sender_name' : sender_name}

		res = insert_func(*args, **keyword_args)

		if not res['status']:
			send_error_email(group.name, res['code'], sender_addr, ADMIN_EMAILS)
			return

		post_id = res['post_id']

		res = upload_message(message, post_id, msg_id)
		if not res['status']:
			logging.debug("Error uploading original post to s3; continuing anyway")

		subject = get_subject(message, res, group.name)
		mail = setup_post(message['From'], subject,	group.name)

		fix_headers(message, mail)
	
		msg_id = res['msg_id']
		mail['message-id'] = msg_id

		to_send =  res['recipients']
		logging.debug('TO LIST: ' + str(to_send))
		
		ccs = email_message.get_all('cc', None)
		if ccs:
			mail['Cc'] = ','.join(ccs)
		
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

					# clear out message other than the headers
					mail.clear()

					membergroup = membergroups.filter(member=recip)[0]
					following = followings.filter(user=recip).exists()
					muting = mutings.filter(user=recip).exists()
					tag_following = tag_followings.filter(user=recip)
					tag_muting = tag_mutings.filter(user=recip)
				
					has_attachments = len(attachments) > 0

					html_ps_blurb = html_ps(g, t, res['post_id'], membergroup, following, muting, tag_following, tag_muting, res['tag_objs'], has_attachments, original_list_email=original_list_email)
					mail.Html = get_new_body(msg_text, html_ps_blurb, 'html')
					
					plain_ps_blurb = plain_ps(g, t, res['post_id'], membergroup, following, muting, tag_following, tag_muting, res['tag_objs'], has_attachments, original_list_email=original_list_email)
					mail.Body = get_new_body(msg_text, plain_ps_blurb, 'plain')

					if membergroup.receive_attachments:
						add_attachments(mail, attachments)

					relay.deliver(mail, To = recip.email)

			fwd_to_lists = ForwardingList.objects.filter(group=g, can_receive=True)

			for l in fwd_to_lists:

				mail.clear()

				# non murmur list, send as usual 
				if HOST not in l.email:

					footer_html = html_forwarded_blurb(g.name, l.email, original_list_email=original_list_email)
					footer_plain = plain_forwarded_blurb(g.name, l.email, original_list_email=original_list_email)

					mail.Html = get_new_body(msg_text, footer_html, 'html')
					mail.Body = get_new_body(msg_text, footer_plain, 'plain')
					add_attachments(mail, attachments)

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
		
def handle_post_squadbox(message, group, host, verified):

	email_message = message_from_string(str(message))
	msg_id = message['Message-ID']

	sender_name, sender_addr = parseaddr(message['From'])
	sender_addr = sender_addr.lower()
	if sender_name == '':
		sender_name = None
	
	subj = message['Subject'].strip()
	message_is_reply = (subj[0:4].lower() == "re: ")

	if message_is_reply:
		original_subj = subj[4:]
		post_subject = "Re: " + re.sub("\[.*?\]", "", subj[4:])
	else:
		original_subj = subj
		post_subject = subj

	res = get_attachments(email_message)
	check = check_attachments(res, group.allow_attachments)

	if not check['status']:
		send_error_email(group.name, check['error'], sender_addr, ADMIN_EMAILS)
		return

	attachments = res['attachments']

	msg_text = get_body(email_message)
	msg_text = check_html_and_plain(msg_text, message_is_reply)

	# initially, assume that it's pending and will go through moderation. 
	status = 'P'
	reason = None

	# deactivated squad - message is auto-approved. 
	if not group.active:
		status = 'A'
		reason = 'deactivated'
		logging.debug("Squad deactivated; automatically approving message")
	else:

		# first try whitelist/blacklist
		status, reason = check_whitelist_blacklist(group, sender_addr)

		# if that didn't give us an answer
		if not reason:

			# see if moderation has been shut off for this user/thread combo. that happens if either:
			# 1) group has setting on to auto-approve posts from a user to thread after their 1st post to thread is approved
			# 2) that setting isn't on, but recipient manually shut off moderation for this user to this thread
			if check_if_sender_approved_for_thread(group.name, sender_addr, original_subj):
				status = 'A'

				# case 1 
				if group.auto_approve_after_first:
					reason = 'auto approve on'
					logging.debug('Sender approved for this thread previously; automatically approving post')
				# case 2
				else:
					reason = "mod off for sender-thread"
					
			else:
				logging.debug('Post needs to be moderated')



	moderators = MemberGroup.objects.filter(group=group, moderator=True)
	if not moderators.exists():
		status = 'A'
		reason = 'no mods'
		logging.debug("Squad has no moderators")

	elif moderators.filter(member__email=sender_addr).exists():
		status = 'A'
		reason = 'is mod'
		logging.debug('Message is from a moderator')

	# if pending or rejected, we need to put it in the DB 
	if status in ['P', 'R']:
		if message_is_reply:
			insert_func = insert_squadbox_reply
		else:
			insert_func = insert_post
			
		args = [group.name, post_subject, msg_text['html'], None, sender_addr, msg_id, verified]
		keyword_args = {'attachments' : attachments, 'sender_name' : sender_name, 'post_status' : status}
    
		res = insert_func(*args, **keyword_args)

		if not res['status']:
			send_error_email(group.name, res['code'], None, ADMIN_EMAILS)
			return

		post_id = res['post_id']

		res = upload_message(message, post_id, msg_id)
		if not res['status']:
			logging.debug("Error uploading original post to s3; continuing anyway")

	# one of following is true: 
	# 1) sender is whitelisted
	# 2) sender is blacklisted, but the user still wants rejected messages. 
	# 3) moderation is turned off for now (inactive group)
	# 4) this group doesn't have any moderators yet
	# 4) group has "auto approve after first post" on, and this sender posted before and got approved 
	# (and the recipient did not subsequently opt back in to moderation for that user)
	# 5) group has "auto approve after first post" off, but owner manually shut off moderation for this sender

	if status == 'A' or (status == 'R' and group.send_rejected_tagged):

		# we can just send it on to the intended recipient, i.e. the admin of the group. 
		admin = MemberGroup.objects.get(group=group, admin=True).member

		new_subj = subj
		if status == 'R':
			new_subj = '[Rejected] ' + new_subj

		mail = MurmurMailResponse(From = message['From'], To = admin.email, Subject = new_subj)

		fix_headers(message, mail)

		ccs = email_message.get_all('cc', None)
		if ccs:
			mail['Cc'] = ','.join(ccs)

		add_attachments(mail, attachments)

		html_blurb = unicode(ps_squadbox(sender_addr, reason, group.name, group.auto_approve_after_first, original_subj, None, True))

		mail.Html = get_new_body(msg_text, html_blurb, 'html')

		plain_blurb = ps_squadbox(sender_addr, reason, group.name, group.auto_approve_after_first, original_subj, None, False)
		mail.Body = get_new_body(msg_text, plain_blurb, 'plain')

		relay.deliver(mail, To = admin.email)

	# send notification to least recently emailed mod if we haven't emailed them in 24 hrs 
	elif status == 'P':
		twenty_four_hours_ago = datetime.now(pytz.utc) + timedelta(days=-1)
		unnotified_mods = moderators.filter(Q(last_emailed__lte=twenty_four_hours_ago) | Q(last_emailed=None))

		if unnotified_mods.exists():
			least_recent = unnotified_mods.order_by('last_emailed')[0]

			outgoing_msg = setup_moderation_post(group.name)
			outgoing_msg['message-id'] = base64.b64encode(group.name + str(datetime.now())).lower() + '@' + BASE_URL

			relay.deliver(outgoing_msg, To=least_recent.member.email)
			logging.debug("sending msg to moderator %s" % least_recent.member.email)

			least_recent.last_emailed = datetime.now(pytz.utc)
			least_recent.save()
		
handler_funcs = {
	'murmur' : handle_post_murmur,
	'squadbox' : handle_post_squadbox,
}

@route("(address)@(host)", address=".+", host=HOST)
@stateless
def handle_post(message, address=None, host=None):
	
	# restart the db connection
	django.db.close_connection()
	
	if '+' in address and '__' in address:
		return

	address = cleanAddress(address)

	reserved = filter(lambda x: address.endswith(x), RESERVED)
	if(reserved):
		return
	
	_, sender_addr = parseaddr(message['From'].lower())
	_, to_addr = parseaddr(message['To'].lower())

	verified = isSenderVerified(message)
	
	group_name = address
	try:
		group = Group.objects.get(name=group_name)
	except Group.DoesNotExist:
		msg = '%s with name %s does not exist.' % (GROUP_OR_SQUAD[WEBSITE], group_name)
		send_error_email(group_name, msg, sender_addr, ADMIN_EMAILS)	
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

	handler_funcs[WEBSITE](message, group, host, verified)


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

	subj_string = message['Subject'].encode('utf-8').lower()
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
