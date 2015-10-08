import email, re
from lamson.server import Relay
from config.settings import *

from lamson_subclass import MurmurMailResponse
from schema.models import Group, MemberGroup, Thread, Following, Mute


'''
MailX Mail Utils and Constants

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''

HOST = 'murmur.csail.mit.edu'
NO_REPLY = 'no-reply' + '@murmur.csail.mit.edu'
POST_SUFFIX = '__post__'
FOLLOW_SUFFIX = '__follow__'
UNFOLLOW_SUFFIX = '__unfollow__'
MUTE_SUFFIX = '__mute__'
UNMUTE_SUFFIX = '__unmute__'
UPVOTE_SUFFIX = '__upvote__'
DOWNVOTE_SUFFIX = '__downvote__'
FETCH_SUFFIX = '__fetch__'

FOLLOW_ADDR = 'http://%s/follow?tid=' % (HOST)
UNFOLLOW_ADDR = 'http://%s/unfollow?tid=' % (HOST)

MUTE_ADDR = 'http://%s/mute?tid=' % (HOST)
UNMUTE_ADDR = 'http://%s/unmute?tid=' % (HOST)

EDIT_SETTINGS_ADDR = 'http://%s/groups/%s/edit_my_settings' % (HOST)

HTML_SUBHEAD = '<div style="border-top:solid thin;padding-top:5px;margin-top:10px">'
HTML_SUBTAIL = '</div>'

PLAIN_SUBHEAD = '***\nMurmur\n'
PLAIN_SUBTAIL = '\n***\n'

RESERVED = ['+create', '+activate', '+deactivate', '+subscribe', '+unsubscribe', '+info', 'help', 'no-reply', 'all', POST_SUFFIX, FOLLOW_SUFFIX, UNFOLLOW_SUFFIX, MUTE_SUFFIX, UNMUTE_SUFFIX, UPVOTE_SUFFIX, DOWNVOTE_SUFFIX, FETCH_SUFFIX]

relay_mailer = Relay(host=relay_config['host'], port=relay_config['port'], debug=1)

ALLOWED_MIMETYPES = ["image/jpeg", "image/bmp", "image/gif", "image/png", "application/pdf"]
MAX_ATTACHMENT_SIZE = 1000000

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


def create_error_email(addr, group_name, host, error):
	mail = setup_post(NO_REPLY, "Error", group_name)
	mail.Body = "Error Message:%s" %(error)
	return mail
		

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
				res['error'] = 'One or more attachments violate allowed mimetypes: jpg, img, png, pdf, and bmp.'
				break
		except Exception, e:
			logging.debug(e)
			continue
	return res
	

def get_body(email_message):
	res = {}
	
	maintype = email_message.get_content_maintype()
	subtype = email_message.get_content_maintype()

	if maintype == 'multipart':
		res['html'] = ''
		res['plain'] = ''
		for part in email_message.get_payload():
			if part.get_content_maintype() == 'text':
				if part.get_content_subtype() == 'html':
					body = part.get_payload()
					body = remove_html_ps(body)
					res['html'] += body
				else:
					body = part.get_payload()
					body = remove_plain_ps(body)
					res['plain'] += body
			elif part.get_content_maintype() == 'multipart':
				for part2 in part.get_payload():
					if part2.get_content_subtype() == 'html':
						body = part2.get_payload()
						body = remove_html_ps(body)
						res['html'] += body
					elif part2.get_content_subtype() == 'plain':
						body = part2.get_payload()
						body = remove_plain_ps(body)
						res['plain'] += body
	elif maintype == 'text':
		if subtype == 'html':
			body = email_message.get_payload()
			body = remove_html_ps(body)
			res['html'] = body
			
		elif subtype == 'text':
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

def html_ps(group, thread, membergroup, following, muting):
	#follow_addr = 'mailto:%s' %(group_name + '+' + FOLLOW_SUFFIX + '@' + HOST)
	#unfollow_addr = 'mailto:%s' %(group_name + '+'  + UNFOLLOW_SUFFIX + '@' + HOST)
	
	tid = thread.id
	
	if membergroup.no_emails or not membergroup.always_follow_thread:
		follow_addr = '%s%s' % (FOLLOW_ADDR, tid)
		unfollow_addr = '%s%s' % (UNFOLLOW_ADDR, tid)
		
		if following:
			content = 'You\'re currently following this thread. <a href="%s">Un-Follow</a> to stop receiving emails from this thread.' % (unfollow_addr)
		else:
			content = 'You currently aren\'t receiving any replies to this thread. <a href="%s">Follow</a> to receive replies to this thread.' % (follow_addr)
	else:
		mute_addr = '%s%s' % (MUTE_ADDR, tid)
		unmute_addr = '%s%s' % (UNMUTE_ADDR, tid)
		if muting:
			content = 'You\'re currently muting this thread. <a href="%s">Un-Mute</a> to start receiving emails to this thread.' % (unmute_addr)
		else:
			content = 'You\'re currently receiving emails to this thread. <a href="%s">Mute</a> to stop receiving emails from this thread.' % (mute_addr)

	addr = EDIT_SETTINGS_ADDR % group.name
	if membergroup.no_emails:
		content += "<BR><BR>You are set to receive no emails from this group, except for the threads you follow. <a href=\"%s\">Change your settings</a>." % (addr)
	elif membergroup.always_follow_thread:
		content += "<BR><BR>You are set to receive only the 1st email from this group, except for the threads you follow. <a href=\"%s\">Change your settings</a>." % (addr)
	else:
		content += "<BR><BR>You are set to receive all emails from this group, except for the threads you mute. <a href=\"%s\">Change your settings</a>." % (addr)
	

	body = '%s%s%s' % (HTML_SUBHEAD, content, HTML_SUBTAIL)
	return body

def plain_ps(group, thread, membergroup, following, muting):
	tid = thread.id
	group_name = group.name
	
	if membergroup.no_emails or not membergroup.always_follow_thread:
		follow_addr = 'mailto:%s' % (group_name + '+' + str(tid) + FOLLOW_SUFFIX + '@' + HOST)
		unfollow_addr = 'mailto:%s' % (group_name + '+' + str(tid) + UNFOLLOW_SUFFIX + '@' + HOST)
		
		if following:
			content = 'You\'re currently following this thread. Un-Follow<%s> to stop receiving emails from this thread.' % (unfollow_addr)
		else:
			content = 'You aren\'t receive any replies to this thread. Follow<%s> to receive replies to this thread.' % (follow_addr)
	else:
		mute_addr = 'mailto:%s' % (group_name + '+' + str(tid) + MUTE_SUFFIX + '@' + HOST)
		unmute_addr = 'mailto:%s' % (group_name + '+' + str(tid) + UNMUTE_SUFFIX + '@' + HOST)
		if muting:
			content = 'You\'re currently muting this thread. Un-Mute<%s> to start receiving emails to this thread.' % (unmute_addr)
		else:
			content = 'You\'re currently receiving emails to this thread. Mute<%s> to stop receiving emails from this thread.' % (mute_addr)
	
	addr = EDIT_SETTINGS_ADDR % group.name
	if membergroup.no_emails:
		content += "\n\nYou are set to receive no emails from this group, except for the threads you follow. Change your settings<%s>." % (addr)
	elif membergroup.always_follow_thread:
		content += "\n\nYou are set to receive only the 1st email from this group, except for the threads you follow. Change your settings<%s>." % (addr)
	else:
		content += "\n\nYou are set to receive all emails from this group, except for the threads you mute. Change your settings<%s>." % (addr)
	
	body = '%s%s%s' % (PLAIN_SUBHEAD, content, PLAIN_SUBTAIL)
	
	return body
