import email, re, time, hashlib, random, dkim, pytz
from lamson.server import Relay
from config.settings import *
from lamson_subclass import MurmurMailResponse
from schema.models import *
from http_handler.settings import BASE_URL, DEFAULT_FROM_EMAIL, WEBSITE
from datetime import datetime, timedelta
from email.utils import *
from email import message_from_string
from hashlib import sha1
from html2text import html2text
from markdown2 import markdown

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

if WEBSITE == 'murmur':
	PLAIN_SUBHEAD = '***\nMurmur\n'
elif WEBSITE == 'squadbox':
	PLAIN_SUBHEAD = '***\nSquadbox\n'

PLAIN_SUBTAIL = '\n***\n'

RESERVED = ['+create', '+activate', '+deactivate', '+subscribe', '+unsubscribe', '+admins', '+info', 'help', 'no-reply', 'all', POST_SUFFIX, FOLLOW_SUFFIX, UNFOLLOW_SUFFIX, MUTE_SUFFIX, UNMUTE_SUFFIX, UPVOTE_SUFFIX, DOWNVOTE_SUFFIX, FETCH_SUFFIX]

relay_mailer = Relay(host=relay_config['host'], port=relay_config['port'], debug=1)

ALLOWED_MIMETYPES = ["image/jpeg", "image/bmp", "image/gif", "image/png", "application/pdf", "application/mspowerpoint",
					"application/x-mspowerpoint", "application/powerpoint", "application/vnd.ms-powerpoint",
					"application/msword", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
					"application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
					"application/vnd.openxmlformats-officedocument.presentationml.presentation", "application/pkcs7-signature"]

ALLOWED_MIMETYPES_STR = 'images (JPEG, BMP, GIF, PNG), PDFs, and Microsoft Office (Word, Excel, Powerpoint) files'

MAX_ATTACHMENT_SIZE = 3000000

# for creating squadbox ps 
SQUADBOX_REASONS = {
	'whitelist' : "This message was auto-approved because the sender %s is on your whitelist.",
	'blacklist' : "This message was auto-rejected because the sender %s is on your blacklist.",
	'no mods' : "This message was auto-approved because your squad currently has no moderators.",
	'deactivated' : "This message was auto-approved because your squad is currently deactivated.",
	'moderator approved' : "This message was approved by your moderator %s.",
	'moderator rejected' : "This message was rejected by your moderator %s.",
	'auto approve on' : "This message was auto-approved because a previous post from %s \
						to this thread was approved.", 
	'mod off for sender-thread' : "This message was auto-approved because you've turned moderation off \
							for posts by %s to this thread.", 
	'is mod' : "This message was auto-approved because it's from one of your moderators.",
}

FUTURE_AUTO_APPROVE = {
	True: "<br><br>Future posts from %s to this thread will be auto-approved.",
	False: "\n\nFuture posts from %s will be auto-approved."
}

MODERATE_ON_LINK = '%s/moderate_user_for_thread_get?group_name=%s&sender=%s&subject=%s&moderate=on'
MODERATE_OFF_LINK = MODERATE_ON_LINK[:-2] + 'off'

MOD_ON = {
	True: " If you would like moderators to continue reviewing this sender's posts to the thread, follow <a href='%s'>this link</a>.",
	False: " If you would like moderators to continue reviewing this sender's posts to the thread, follow this link: <%s>."
}

MOD_BACK_ON = {
	True: " To turn it back on, follow <a href='%s'>this link</a>.",
	False: " To turn it back on, follow this link: <%s>."
}


MOD_OFF = {
	True: " To turn moderation off for future posts from %s to this thread, follow <a href='%s'>this link</a>.",
	False: " To turn moderation off for future posts from %s to this thread, follow this link: <%s>."
}

EDIT_WL_BL_MODS = {
	True: "<br><br>To edit your whitelist, blacklist, or moderators, visit the <a href='%s'>squad page</a>.",
	False: "\n\nTo edit your whitelist, blacklist, or moderators, visit the squad page: <%s>."
}

REACTIVATE = {
	True: "<br><br>To reactivate your squad, visit the <a href='%s'>squad page</a>.",
	False: "\n\nTo reactivate your squad, visit the squad page: <%s>."
}

EDIT_AUTO_APPROVE = {
	True: "<br>To edit your thread auto-approval settings, visit the <a href='%s'>squad settings page</a>.",
	False: "\nTo edit your thread auto-approval settings, visit the squad settings page <%s>."
}

SQUAD_PAGE_LINK = '%s/groups/%s'
SQUAD_SETTINGS_LINK = SQUAD_PAGE_LINK + '/edit_group_info'

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

def setup_moderation_post(group_name):

	subject = 'New posts to Squadbox squad %s require approval' % group_name 
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

	pending_count = Post.objects.filter(group__name=group_name, status='P').count()

	body_base = 'As of now, there are %s pending posts. To view all of them, visit the ' %  pending_count
	plain_body = body_base + "moderation queue: %s/mod_queue/%s" % (BASE_URL, group_name)
	html_body = body_base + "<a href='%s/mod_queue/%s'>moderation queue</a>." % (BASE_URL, group_name)

	blurb = "You're receiving this message because you're a moderator of the squad %s." % group_name
	html_ps_blurb = '%s%s%s' % (HTML_SUBHEAD, blurb, HTML_SUBTAIL)
	plain_ps_blurb = '%s%s%s' % (PLAIN_SUBHEAD, blurb, PLAIN_SUBTAIL)

	mail.Html = html_body + html_ps_blurb
	mail.Body = plain_body + plain_ps_blurb
	
	return mail

def send_email(subject, from_addr, to_addr, body_plain=None, body_html=None):
	mail = MurmurMailResponse(From = from_addr, Subject = subject)
	if body_plain:
		mail.Body = body_plain
	if body_html:
		mail.Html = body_html

	relay_mailer.deliver(mail, To = to_addr)

def send_error_email(group_name, error, user_addr, admin_emails):
	if user_addr:
		body = "You tried to post to: %s. Error Message: %s" % (group_name, error)
		send_email(subject = "Error", from_addr = NO_REPLY, to_addr = user_addr, body_plain = body)
	if admin_emails:
		body = "User %s tried to post to: %s. Error Message: %s" % (user_addr, group_name, error)
		send_email(subject = "Error", from_addr = NO_REPLY, to_addr = ADMIN_EMAILS, body_plain = body)

def check_attachments(attachments, attachments_allowed):

	res = {'status' : True, 'error' : None}

	if WEBSITE == 'murmur':
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

	text = message_text[plain_or_html]

	if isinstance(text, unicode):
		logging.debug("it's unicode, no need to change")
		new_body = text + ps_blurb

	else:
		logging.debug("not unicode, convert using utf-8")
		converted_text = unicode(text, "utf-8", "ignore")
		new_body = converted_text + ps_blurb

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
	
	for part in email_message.walk():

		disposition = part.get('content-disposition')

		if not disposition or not disposition.split(';')[0] in ['inline', 'attachment']:
			logging.debug("no disposition or not attachment; skip")
			continue

		content_type = part.get_content_type()
		part_data = part.get_payload(decode=True)

		if content_type in ALLOWED_MIMETYPES or WEBSITE == 'squadbox':
			if len(part_data) < MAX_ATTACHMENT_SIZE or WEBSITE == 'squadbox':

				content_id = part.get('content-id')

				res['attachments'].append({'content': part_data,
										   'mime': content_type,
										   'filename': part.get_filename(),
										   'disposition': disposition,
										   'id': content_id})
			else:
				res['error'] = 'One or more attachments exceed size limit of 3MB. Please use a separate service and send a link instead.'

		else:
			res['error'] = 'One or more attachments was an unsupported filetype. We support %s.' % ALLOWED_MIMETYPES_STR

	return res
	

def get_body(email_message):

	res = {'html' : '', 'plain' : ''}

	for part in email_message.walk():
		if part.get_content_maintype() == 'text':

			body = part.get_payload(decode=True)

			subtype = part.get_content_subtype()
			if subtype == 'plain':
				res['plain'] += remove_plain_ps(body)
			elif subtype == 'html':
				res['html'] += remove_html_ps(body)

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

def ps_squadbox(sender, reason, squad_name, squad_auto_approve, subject, mod_email, HTML):

	mod_on = MODERATE_ON_LINK % (BASE_URL, squad_name, sender, subject)
	mod_off = MODERATE_OFF_LINK % (BASE_URL, squad_name, sender, subject)
	squad_link = SQUAD_PAGE_LINK % (BASE_URL, squad_name)
	settings_link = SQUAD_SETTINGS_LINK % (BASE_URL, squad_name)

	content = SQUADBOX_REASONS[reason]

	if reason in ['whitelist', 'blacklist']:
		content %= sender
		content += EDIT_WL_BL_MODS[HTML] % squad_link

	elif reason == 'auto approve on':
		content %= sender
		content += MOD_ON[HTML] % mod_on + EDIT_AUTO_APPROVE[HTML] % settings_link

	elif reason == 'moderator approved':
		content %= mod_email
		if squad_auto_approve:
			content += FUTURE_AUTO_APPROVE[HTML] % sender + MOD_ON[HTML] % mod_on + EDIT_AUTO_APPROVE[HTML] % settings_link
		else:
			content += MOD_OFF[HTML] % (sender, mod_off)

	elif reason == 'moderator rejected':
		content %= mod_email 

	elif reason in ['no mods', 'is mod']:
		content += EDIT_WL_BL_MODS[HTML] % squad_link

	elif reason == 'mod off for sender-thread':
		content %= sender
		content += MOD_BACK_ON[HTML] % mod_on

	elif reason == 'deactivated':
		content += REACTIVATE[HTML] % squad_link

	if HTML:
		return '%s%s%s' % (HTML_SUBHEAD, content, HTML_SUBTAIL)
	else:
		return '%s%s%s' % (PLAIN_SUBHEAD, content, PLAIN_SUBTAIL)

def html_ps(group, thread, post_id, membergroup, following, muting, tag_following, tag_muting, tags, had_attachments, original_list_email=None):
	#follow_addr = 'mailto:%s' %(group_name + '+' + FOLLOW_SUFFIX + '@' + HOST)
	#unfollow_addr = 'mailto:%s' %(group_name + '+'  + UNFOLLOW_SUFFIX + '@' + HOST)
	content = ""

	if original_list_email:
		content += "This post was sent to this group via the mailing list %s. <BR><BR>" % (original_list_email)

	if had_attachments and not membergroup.receive_attachments:
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
	return unicode(body)

def plain_ps(group, thread, post_id, membergroup, following, muting, tag_following, tag_muting, tags, had_attachments, original_list_email=None):

	content = ""
	if original_list_email:
		content += "This post was sent to this group via the mailing list %s. \n\n" % (original_list_email)

	if had_attachments and not membergroup.receive_attachments:
		content += "This message came with attachments, which you have turned off. To see the attachments, view the original post:\n"

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

def isSenderVerified(message):
	# check 1: DKIM
	email_message = message.original
	_, sender_addr = parseaddr(message['From'].lower())
	_, to_addr = parseaddr(message['To'].lower())
	verified = dkim.verify(email_message)

	# import spf
	# check 2: SPF - TODO: SPF not implemented - need to find incoming mail server IP address
	# if not verified:
	# 	spf_i = ""
	# 	spf_h = ""
	# 	spf_s = sender_addr
	# 	result = spf.check(spf_i, spf_s, spf_h)
	# 	if result[0] == "pass":
	# 		verified = True

	if not verified:
		# check if UserProfile has a hash, if not generate one and send it to them
		try:
			user = UserProfile.objects.get(email=sender_addr)
		except UserProfile.DoesNotExist:
			user = None
		if user:
			# TODO: create new user here if it doesn't exist or otherwise handle posts from non-users
			# for now just mark as un-verified if DKIM and SPF fail
			if not user.hash:
				salt = hashlib.sha1(str(random.random())+str(time.time())).hexdigest()[:5]
				new_hash = hashlib.sha1(sender_addr+to_addr+salt).hexdigest()[:20]
				user.hash = new_hash
				user.save()
				#mail = MurmurMailResponse(From = NO_REPLY, Subject = "Please use your secret code in future emails")
				#mail.Body = "In future, to ensure your message is delivered, please include the code %s within the address of your emails, before the '@' symbol and after a '+' symbol. E.g. if you are emailing testgroup@%s, you should now email testgroup+%s@%s to ensure your email is verified as coming directly from you, and thus delivered correctly." % (new_hash, HOST, new_hash, HOST)
				#relay.deliver(mail, To = sender_addr)
			hash_group = re.search(r'\+(.{20,40}?)\@', to_addr)
			if hash_group:
				sender_hash = hash_group.group(1)
				if sender_hash == user.hash:
					verified = True
	return verified

def cleanAddress(address):
	return address.split('+')[0].lower()


def check_whitelist_blacklist(group, sender_addr):
	white_or_blacklist = WhiteOrBlacklist.objects.filter(group=group, email=sender_addr)

	if white_or_blacklist.exists():
		w_or_b = white_or_blacklist[0]
		if w_or_b.blacklist:
			return ('R', 'blacklist')
		elif w_or_b.whitelist:
			return ('A', 'whitelist')

	return ('P', None)

def check_html_and_plain(msg_text, message_is_reply):

	if message_is_reply:
		if 'html' in msg_text:
			msg_text['html'] = remove_html_ps(msg_text['html'])
		if 'plain' in msg_text:
			msg_text['plain'] = remove_plain_ps(msg_text['plain'])

	if 'html' not in msg_text or msg_text['html'] == '':
		msg_text['html'] = markdown(msg_text['plain'])
	if 'plain' not in msg_text or msg_text['plain'] == '':
		try:
			msg_text['plain'] = html2text(msg_text['html'])
		except UnicodeDecodeError:
			pass

	return msg_text

def check_duplicate(message, group, sender_addr):

	# check if we already got a post to this group with the same message_id
	existing_post_matching_id = Post.objects.filter(msg_id=message['Message-ID'], group=group)
	if existing_post_matching_id.exists():
		logging.debug("Already received post with same msg-id to this group")
		return True

	# or di we get one with same sender and subject in the last ten minutes? 
	# (this might happen if we get a post via multiple mailing lists, for example, 
	# and the mailing list changes the ID.)
	ten_minutes_ago = datetime.now(pytz.utc) + timedelta(minutes=-10)
	existing_post_recent = Post.objects.filter(poster_email=sender_addr, group=group, 
									subject=message['Subject'], timestamp__gte = ten_minutes_ago)
	if existing_post_recent.exists():
		logging.debug("Post with same sender and subject sent to this group < 10 min ago")
		return True

	# this is the case where we forward a message to a google group, and it forwards back to us
	if 'X-Original-Sender' in message and message['X-Original-Sender'].split('@')[0] == group.name:
		logging.debug('This message originally came from this list; not reposting')
		return True

	return False

def check_if_can_post_murmur(group, sender_addr, possible_list_addresses):

	forwarding_list = None

	logging.debug("pssible list addresses: " + str(possible_list_addresses))

	# if you're a member of this group, you can post
	membergroup = MemberGroup.objects.filter(group=group, member__email=sender_addr)
	if membergroup.exists():
		return {'can_post' : True, 'reason' : 'is_member', 'which_user' : membergroup[0].member}

	# otherwise, you can only post if you're posting via a forwarding list
	forwarding_list = ForwardingList.objects.filter(email__in=possible_list_addresses, group=group, can_post=True)

	if forwarding_list.exists():
		return {'can_post' : True, 'reason' : 'via_list', 'which_list' : forwarding_list[0]}

	return {'can_post' : False, 'reason' : 'not_member'}

def fix_headers(message, mail):
	if 'References' in message:
			mail['References'] = message['References']

	# a message's own ID shouldn't show up in its references. commenting out for now.
	# elif 'message-id' in message:
	# 	mail['References'] = message['message-id']	

	# a message can't be in reply to itself. if it's a reply to a previous message and needs 
	# this header, then that value is contained in the received message's in-reply-to. so
	# we should just copy it over if it exists, and that's it. commenting out for now. 

	# if 'in-reply-to' not in message:
	# 	mail["In-Reply-To"] = message['message-id']

	if 'in-reply-to' in message:
		mail['In-Reply-To'] = message['In-Reply-To']

	mail['Message-ID'] = message['Message-ID']

def add_attachments(mail, attachments):
	for attachment in attachments:
		mail.attach(filename= attachment['filename'],
					content_type=attachment['mime'],
					data=attachment['content'],
					disposition=attachment['disposition'],
					id=attachment['id'])

def get_sender_subject_hash(sender_addr, subject):
	data = '%s|%s' % (sender_addr, subject)
	return sha1(data.encode()).hexdigest()

def check_if_sender_approved_for_thread(group_name, sender_addr, subject):
	hashed = get_sender_subject_hash(sender_addr, subject)
	return ThreadHash.objects.filter(sender_subject_hash=hashed, group__name=group_name, moderate=False).exists()

def check_if_sender_moderated_for_thread(group_name, sender_addr, subject):
	hashed = get_sender_subject_hash(sender_addr, subject)
	return ThreadHash.objects.filter(sender_subject_hash=hashed, group__name=group_name, moderate=True).exists()
