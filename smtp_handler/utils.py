import email, re, time, hashlib, random
from lamson.server import Relay
from config.settings import *
from lamson_subclass import MurmurMailResponse
from schema.models import Group, MemberGroup, Thread, Following, Mute, UserProfile
from http_handler.settings import BASE_URL, DEFAULT_FROM_EMAIL

'''
Murmur Mail Utils and Constants

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''

HOST = BASE_URL
NO_REPLY = DEFAULT_FROM_EMAIL
POST_SUFFIX = '__post__'
FOLLOW_SUFFIX = '__follow__'
UNFOLLOW_SUFFIX = '__unfollow__'
MUTE_SUFFIX = '__mute__'
UNMUTE_SUFFIX = '__unmute__'
FOLLOW_TAG_SUFFIX = '__followtag__'
UNFOLLOW_TAG_SUFFIX = '__unfollowtag__'
MUTE_TAG_SUFFIX = '__mutetag__'
UNMUTE_TAG_SUFFIX = '__unmutetag__'
UPVOTE_SUFFIX = '__upvote__'
DOWNVOTE_SUFFIX = '__downvote__'
FETCH_SUFFIX = '__fetch__'

ADMIN_EMAILS = ['axz@mit.edu', 'kmahar@mit.edu']

FOLLOW_ADDR = 'http://%s/follow?tid=' % (HOST)
UNFOLLOW_ADDR = 'http://%s/unfollow?tid=' % (HOST)

FOLLOW_TAG_ADDR = 'http://%s/follow_tag_get?tag=' % (HOST)
UNFOLLOW_TAG_ADDR = 'http://%s/unfollow_tag_get?tag=' % (HOST)
MUTE_TAG_ADDR = 'http://%s/mute_tag_get?tag=' % (HOST)
UNMUTE_TAG_ADDR = 'http://%s/unmute_tag_get?tag=' % (HOST)

MUTE_ADDR = 'http://%s/mute?tid=' % (HOST)
UNMUTE_ADDR = 'http://%s/unmute?tid=' % (HOST)

UPVOTE_ADDR = 'http://%s/upvote_get?tid=%s&post_id=%s' 

SUBSCRIBE_ADDR = 'http://%s/subscribe_get?group_name=%s'
UNSUBSCRIBE_ADDR = 'http://%s/unsubscribe_get?group_name=%s'

EDIT_SETTINGS_ADDR = 'http://%s/groups/%s/edit_my_settings'

PERMALINK_POST = 'http://%s/thread?tid=%s&post_id=%s'

HTML_SUBHEAD = '<div style="border-top:solid thin;padding-top:5px;margin-top:10px">'
HTML_SUBTAIL = '</div>'

PLAIN_SUBHEAD = '***\nMurmur\n'
PLAIN_SUBTAIL = '\n***\n'

RESERVED = ['+create', '+activate', '+deactivate', '+subscribe', '+unsubscribe', '+admins', '+info', 'help', 'no-reply', 'all', POST_SUFFIX, FOLLOW_SUFFIX, UNFOLLOW_SUFFIX, MUTE_SUFFIX, UNMUTE_SUFFIX, UPVOTE_SUFFIX, DOWNVOTE_SUFFIX, FETCH_SUFFIX]

relay_mailer = Relay(host=relay_config['host'], port=relay_config['port'], debug=1)

ALLOWED_MIMETYPES = ["image/jpeg", "image/bmp", "image/gif", "image/png", "application/pdf", "application/mspowerpoint",
					"application/x-mspowerpoint", "application/powerpoint", "application/vnd.ms-powerpoint",
					"application/msword", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
					"application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
					"application/vnd.openxmlformats-officedocument.presentationml.presentation"]
MAX_ATTACHMENT_SIZE = 3000000

def setup_post(From, Subject, group_name):
	
	post_addr = '%s <%s>' %(group_name, group_name + '@' + HOST)

	mail = MurmurMailResponse(From = From, 
						To = post_addr, 
						Subject = Subject)

	mail.update({
		"Sender": post_addr, 
		"Reply-To": post_addr,
		"List-Id": post_addr,
		"List-Unsubscribe": "<mailto:%s+unsubscribe@%s>" % (group_name, HOST),
		"List-Archive": "<http://%s/groups/%s/>" % (HOST, group_name),
		"List-Post": "<mailto:%s>" % (group_name + '@' + HOST),
		"List-Help": "<mailto:help@%s>" % HOST,
		"List-Subscribe": "<mailto:%s+subscribe@%s>" % (group_name, HOST),
		"Return-Path": post_addr, 
		"Precedence": 'list',
	})
	
	return mail

def setup_moderation_post(group_name, msg_text, post_id):

	subject = 'Post to Squadbox group %s requires approval' % group_name 
	to = '%s Moderators <%s+mods@%s>' % (group_name, group_name, HOST)
	from_addr = 'Squadbox Notifications <%s+notifications@%s>' % (group_name, HOST)

	mail = MurmurMailResponse(From=from_addr, To=to, Subject=subject)
	mail.update({
		"Sender" : from_addr,
		"Reply-To" : from_addr,
		"List-Id" : from_addr,
		"Return-Path": from_addr,
		"Precedence": 'list'
		})

	html_ps_blurb = 'replace this with a blurb later on!'
	html_ps_blurb = unicode(html_ps_blurb)
	mail.Html = get_new_body(msg_text, html_ps_blurb, 'html')
	
	plain_ps_blurb = 'replace this with a blurb later on!'
	mail.Body = get_new_body(msg_text, plain_ps_blurb, 'plain')
		
	return mail

def send_error_email(group_name, error, user_addr, admin_emails):
	mail = MurmurMailResponse(From = NO_REPLY, Subject = "Error")
	mail.Body = "You tried to post to: %s. Error Message: %s" % (group_name, error)
	if user_addr:
		relay.deliver(mail, To = user_addr)
	if admin_emails:
		relay.deliver(mail, To = ADMIN_EMAILS)

def check_attachments(attachments, attachments_allowed):

	res = {'status' : True, 'error' : None}

	if len(attachments['attachments']) > 0 and not attachments_allowed:
		logging.debug("No attachments allowed for this group")
		res['error'] = "No attachments allowed for this group."
		res['status'] = False
		return res

	if attachments['error'] != '':
		logging.debug(attachments['error'])
		res['error'] = attachments['error']
		res['status'] = False

	return res

def get_subject(message, msg_res, group_name):
	if message['Subject'][0:4].lower() != "re: ":
		subj_tag = ''
		for tag in msg_res['tags']:
			subj_tag += '[%s]' % tag['name']
			
		trunc_subj = re.sub("\[.*?\]", "", message['Subject'])
		subject = '[%s]%s %s' %(group_name, subj_tag, trunc_subj)
	else:
		subject = message['Subject']

	return subject

def get_new_body(message_text, ps_blurb, plain_or_html):
	try:
		# assume email is in utf-8
		new_body = unicode(message_text[plain_or_html], "utf-8", "ignore")
		new_body = new_body + ps_blurb
	except UnicodeDecodeError:
		#then try default (ascii)
		logging.debug('unicode decode error')
		new_body = unicode(message_text[plain_or_html], errors="ignore")
		new_body = new_body + ps_blurb
	except TypeError:
		logging.debug('decoding Unicode is not supported')
		new_body = message_text[plain_or_html]
		new_body = new_body + ps_blurb

	return new_body

		
def get_direct_recips(email_message):
	tos = email_message.get_all('to', [])
	ccs = email_message.get_all('cc', [])
	bccs = email_message.get_all('bcc', [])
	resent_tos = email_message.get_all('resent-to', [])
	resent_ccs = email_message.get_all('resent-cc', [])
	resent_bccs = email_message.get_all('resent-bcc', [])
	all_recipients = email.utils.getaddresses(tos + ccs + bccs + resent_tos + resent_ccs + resent_bccs)
	emails = [recip[1] for recip in all_recipients]
	return emails

def get_attachments(email_message):
	res = {'attachments': [],
		   'error': ''}
	
	for i in range(1, len(email_message.get_payload())):
		try:
			attachment = email_message.get_payload()[i]
			attachment_type = attachment.get_content_type()
			content_id = attachment.get('content-id')
			disposition = attachment.get('content-disposition')
			if disposition:
				disposition = disposition.split(';')[0]
				if disposition not in ['inline', 'attachment']:
					continue
			else:
				continue
			
			attachment_data = attachment.get_payload(decode=True)
			if attachment_type in ALLOWED_MIMETYPES:
				if len(attachment_data) < MAX_ATTACHMENT_SIZE:
					res['attachments'].append({'content': attachment_data,
											   'mime': attachment_type,
											   'filename': attachment.get_filename(),
											   'disposition': disposition,
											   'id': content_id})
				else:
					res['error'] = 'One or more attachments exceed size limit of 1MB. Please use a separate service and send a link to the list instead.'
					break
			else:
				# just send the email without the attachment
				#res['error'] = 'One or more attachments violate allowed mimetypes: jpg, img, png, pdf, and bmp.'
				#break
				continue
		except Exception, e:
			logging.debug(e)
			continue
	return res
	

def get_body(email_message):
	res = {}

	maintype = email_message.get_content_maintype()
	subtype = email_message.get_content_subtype()

	if maintype == 'multipart':
		res['html'] = ''
		res['plain'] = ''

		for part in email_message.get_payload():
			d = (part['Content-Transfer-Encoding'] == 'base64')
			if part.get_content_maintype() == 'text':
				if part.get_content_subtype() == 'html':
					body = part.get_payload(decode=d)
					body = remove_html_ps(body)
					res['html'] += body
				else:
					body = part.get_payload(decode=d)
					body = remove_plain_ps(body)
					res['plain'] += body
			elif part.get_content_maintype() == 'multipart':
				for part2 in part.get_payload():
					if part2.get_content_subtype() == 'html':
						body = part2.get_payload(decode=d)
						body = remove_html_ps(body)
						res['html'] += body
					elif part2.get_content_subtype() == 'plain':
						body = part2.get_payload(decode=d)
						body = remove_plain_ps(body)
						res['plain'] += body
	elif maintype == 'text':
		if subtype == 'html':
			body = email_message.get_payload()
			body = remove_html_ps(body)
			res['html'] = body
			
		elif subtype == 'plain':
			body = email_message.get_payload()
			body = remove_plain_ps(body)
			res['plain'] = body
	return res


def remove_html_ps(body):
	head, _, x = body.partition(HTML_SUBHEAD)
	_, _, tail = x.partition(HTML_SUBTAIL)
	return head + tail

def remove_plain_ps(body):
	head, _, x = body.partition(PLAIN_SUBHEAD)
	_, _, tail = x.partition(PLAIN_SUBTAIL)
	return head + tail

def _insert_plain_tag_line(group, tags, membergroup, tag_following, tag_muting):
	tag_str = 'Tags: | '
	
	if tags.count() == 0:
		return ''
	
	if membergroup.no_emails or not membergroup.always_follow_thread:
		follow_tags = []
		for f in tag_following:
			follow_tags.append(f.tag.name)
			unfollow_tag_email = 'mailto:%s' % (group.name + '+' + f.tag.name + UNFOLLOW_TAG_SUFFIX + '@' + HOST)
			tag_str += 'Unfollow %s<%s> | ' % (f.tag.name, unfollow_tag_email)
		
		for tag in tags:
			if tag.name not in follow_tags:
				follow_tag_email = 'mailto:%s' % (group.name + '+' + tag.name + FOLLOW_TAG_SUFFIX + '@' + HOST)
				tag_str += ' Follow %s<%s> |' % (tag.name, follow_tag_email)
	else:
		mute_tags = []
		for f in tag_muting:
			mute_tags.append(f.tag.name)
			unmute_tag_email = 'mailto:%s' % (group.name + '+' + f.tag.name + UNMUTE_TAG_SUFFIX + '@' + HOST)
			tag_str += 'Unmute %s<%s> | ' % (f.tag.name, unmute_tag_email)
		
		for tag in tags:
			if tag.name not in mute_tags:
				mute_tag_email = 'mailto:%s' % (group.name + '+' + tag.name + MUTE_TAG_SUFFIX + '@' + HOST)
				tag_str += ' Mute %s<%s> |' % (tag.name, mute_tag_email)
	return tag_str

def _insert_tag_line(group, tags, membergroup, tag_following, tag_muting):
	tag_str = 'Tags: | '
	
	if tags.count() == 0:
		return ''
	
	if membergroup.no_emails or not membergroup.always_follow_thread:
		follow_tags = []
		for f in tag_following:
			follow_tags.append(f.tag.name)
			tag_str += '<a href="%s%s&group=%s">Unfollow %s</a> | ' % (UNFOLLOW_TAG_ADDR, f.tag.name, group.name, f.tag.name)
		
		for tag in tags:
			if tag.name not in follow_tags:
				tag_str += ' <a href="%s%s&group=%s">Follow %s</a> |' % (FOLLOW_TAG_ADDR, tag.name, group.name, tag.name)
	else:
		mute_tags = []
		for f in tag_muting:
			mute_tags.append(f.tag.name)
			tag_str += '<a href="%s%s&group=%s">Unmute %s</a> | ' % (UNMUTE_TAG_ADDR, f.tag.name, group.name, f.tag.name)
		
		for tag in tags:
			if tag.name not in mute_tags:
				tag_str += ' <a href="%s%s&group=%s">Mute %s</a> |' % (MUTE_TAG_ADDR, tag.name, group.name, tag.name)
	return tag_str


def html_forwarded_blurb(group_name, to_list, original_list_email=None):
	content = ''
	if original_list_email:
		content += 'This post was sent to %s@%s via the mailing list %s.<BR>' % (group_name, HOST, original_list_email)
	content += "You're receiving this message because the Murmur group %s (%s@%s) is set to forward \
			posts to a mailing list you are a member of (%s)." % (group_name, group_name, HOST, to_list)
	content += "<BR><BR><a href='http://murmur.csail.mit.edu'>Learn more about Murmur</a>"
	body = '%s%s%s' % (HTML_SUBHEAD, content, HTML_SUBTAIL)
	return body

def plain_forwarded_blurb(group_name, to_list, original_list_email=None):
	content = ''
	if original_list_email:
		content += 'This post was sent to %s@%s via the mailing list %s.\n' % (group_name, HOST, original_list_email)
	content += "You\'re receiving this message because the Murmur group %s (%s@%s) is set to forward \
			posts to a mailing list you are a member of (%s)." % (group_name, group_name, HOST, to_list)
	content += "\n\nLearn more about Murmur <http://murmur.csail.mit.edu>"
	body = '%s%s%s' % (HTML_SUBHEAD, content, HTML_SUBTAIL)
	return body

def html_ps(group, thread, post_id, membergroup, following, muting, tag_following, tag_muting, tags, original_list_email=None):
	#follow_addr = 'mailto:%s' %(group_name + '+' + FOLLOW_SUFFIX + '@' + HOST)
	#unfollow_addr = 'mailto:%s' %(group_name + '+'  + UNFOLLOW_SUFFIX + '@' + HOST)
	content = ""

	if original_list_email:
		content += "This post was sent to this group via the mailing list %s. <BR><BR>" % (original_list_email)

	if not membergroup.receive_attachments:
		content += "This message came with attachments, which you have turned off. To see the attachments, view the original post:<br />"
	tid = thread.id
	permalink = PERMALINK_POST % (HOST, tid, post_id)
	content += '<a href="%s">Link to Post</a> | ' % (permalink)
	upvote_addr = UPVOTE_ADDR % (HOST, tid, post_id)
	content += '<a href="%s">Upvote Post</a><BR><BR>' % (upvote_addr)
	
	if membergroup.no_emails or not membergroup.always_follow_thread:
		follow_addr = '%s%s' % (FOLLOW_ADDR, tid)
		unfollow_addr = '%s%s' % (UNFOLLOW_ADDR, tid)
		
		if following:
			content += 'You\'re currently following this thread. <a href="%s">Un-Follow thread</a>.<BR>' % (unfollow_addr)
		else:
			if tag_following.count() > 0:
				tag_names = [f.tag.name for f in tag_following]
				if len(tag_names) > 1:
					n_str = ', '.join(tag_names)
					content += 'You\'re currently following the tags %s. <BR>' % (n_str)
				else:
					content += 'You\'re currently following the tag %s. <BR>' % (tag_names[0])
			else:
				content += 'You currently aren\'t receiving any replies to this thread. <a href="%s">Follow thread</a>.<BR>' % (follow_addr)
	else:
		mute_addr = '%s%s' % (MUTE_ADDR, tid)
		unmute_addr = '%s%s' % (UNMUTE_ADDR, tid)
		if muting:
			content += 'You\'re currently muting this thread. <a href="%s">Un-Mute thread</a>.<BR>' % (unmute_addr)
		else:
			if tag_muting.count() > 0:
				tag_names = [f.tag.name for f in tag_muting]
				if len(tag_names) > 1:
					n_str = ', '.join(tag_names)
					content += 'You\'re currently muting the tags %s. <BR>' % (n_str)
				else:
					content += 'You\'re currently muting the tag %s. <BR>' % (tag_names[0])
			else:
				content += 'You\'re currently receiving emails to this thread. <a href="%s">Mute thread</a>.<BR>' % (mute_addr)
		
	content += _insert_tag_line(group, tags, membergroup, tag_following, tag_muting)

	addr = EDIT_SETTINGS_ADDR % (HOST, group.name)
	if membergroup.no_emails:
		content += "<BR><BR>You are set to receive no emails from this group, except for the threads you follow. <BR><a href=\"%s\">Change your settings</a>" % (addr)
	elif membergroup.always_follow_thread:
		content += "<BR><BR>You are set to receive all emails from this group, except for the threads you mute. <BR><a href=\"%s\">Change your settings</a>" % (addr)
	else:
		content += "<BR><BR>You are set to receive only the 1st email from this group, except for the threads you follow. <BR><a href=\"%s\">Change your settings</a>" % (addr)

	unsubscribe_addr = UNSUBSCRIBE_ADDR % (HOST, group.name)
	content += ' | ''<a href=\"%s\">Unsubscribe</a>' % unsubscribe_addr

	body = '%s%s%s' % (HTML_SUBHEAD, content, HTML_SUBTAIL)
	return body

def plain_ps(group, thread, post_id, membergroup, following, muting, tag_following, tag_muting, tags, original_list_email=None):

	content = ""
	if original_list_email:
		content += "This post was sent to this group via the mailing list %s. \n\n" % (original_list_email)

	tid = thread.id
	group_name = group.name
	
	permalink = PERMALINK_POST % (HOST, tid, post_id)
	content += 'Link to Post<%s>\n\n' % (permalink)
	upvote_addr = 'mailto:%s' % (group_name + '+' + str(post_id) + UPVOTE_SUFFIX + '@' + HOST)
	content += 'Upvote Post<%s>\n\n' % (upvote_addr)
	
	if membergroup.no_emails or not membergroup.always_follow_thread:
		follow_addr = 'mailto:%s' % (group_name + '+' + str(tid) + FOLLOW_SUFFIX + '@' + HOST)
		unfollow_addr = 'mailto:%s' % (group_name + '+' + str(tid) + UNFOLLOW_SUFFIX + '@' + HOST)

		if following:
			content += 'You\'re currently following this thread. Un-Follow thread<%s>.\n' % (unfollow_addr)
		else:
			if tag_following.count() > 0:
				tag_names = [m.tag.name for m in tag_muting]
				if len(tag_names) > 1:
					n_str = ', '.join(tag_names)
					content += 'You\'re currently following the tags %s. \n' % (n_str)
				else:
					content += 'You\'re currently following the tag %s. \n' % (tag_names[0])
			else:
				content += 'You aren\'t receive any replies to this thread. Follow thread<%s>.\n' % (follow_addr)
	else:
		mute_addr = 'mailto:%s' % (group_name + '+' + str(tid) + MUTE_SUFFIX + '@' + HOST)
		unmute_addr = 'mailto:%s' % (group_name + '+' + str(tid) + UNMUTE_SUFFIX + '@' + HOST)

		if muting:
			content += 'You\'re currently muting this thread. Un-Mute thread<%s>.\n' % (unmute_addr)
		else:
			if tag_muting.count() > 0:
				tag_names = [m.tag.name for m in tag_muting]
				if len(tag_names) > 1:
					n_str = ', '.join(tag_names)
					content += 'You\'re currently muting the tags %s. \n' % (n_str)
				else:
					content += 'You\'re currently muting the tag %s. \n' % (tag_names[0])
			else:
				content += 'You\'re currently receiving emails to this thread. Mute thread<%s>.\n' % (mute_addr)
		
	content += _insert_plain_tag_line(group, tags, membergroup, tag_following, tag_muting)
	
	addr = EDIT_SETTINGS_ADDR % (HOST, group.name)
	if membergroup.no_emails:
		content += "\n\nYou are set to receive no emails from this group, except for the threads you follow. \nChange your settings<%s>" % (addr)
	elif membergroup.always_follow_thread:
		content += "\n\nYou are set to receive all emails from this group, except for the threads you mute. \nChange your settings<%s>" % (addr)
	else:
		content += "\n\nYou are set to receive only the 1st email from this group, except for the threads you follow. \nChange your settings<%s>" % (addr)

	unsubscribe_addr = UNSUBSCRIBE_ADDR % (HOST, group.name)
	content += '\n\nUnsubscribe<%s>' % unsubscribe_addr
		
	body = '%s%s%s' % (PLAIN_SUBHEAD, content, PLAIN_SUBTAIL)
	
	return body

def isSenderVerified(sender_addr, to_addr):
	verified = False

	# TODO: implement DKIM check here on sender_addr using dkimpy before checking the old-fashioned hash way

	if not verified:
		# check if userprofile has a hash, if not generate one and send it to them

		user = UserProfile.objects.get(email=sender_addr)
		if not user.hash:
			salt = hashlib.sha1(str(random.random())+str(time.time())).hexdigest()[:5]
			new_hash = hashlib.sha1(sender_addr+to_addr+salt).hexdigest()
			user.hash = new_hash
			user.save()
			mail = MurmurMailResponse(From = NO_REPLY, Subject = "Your new secret email for sender verification")
			mail.Body = "In future, please email with hash %s for your incoming mail to be verified." % (new_hash)
			relay.deliver(mail, To = sender_addr)

		hash_group = re.search(r'\+(.\{40}\?)\@', to_addr)
		if hash_group:
			sender_hash = hash_group.group(0)
			if sender_hash == user.hash:
				verified = True

	return verified

def cleanEmailAddress(email):
	cleanEmail = email
	hash_group = re.search(r'\+(.\{40}\?)\@', to_addr)
	if hash_group:
		sender_hash = hash_group.group(0)
		re.sub('+'+sender_hash, '', cleanEmail)
	return cleanEmail