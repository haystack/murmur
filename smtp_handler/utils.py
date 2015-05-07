import email, re
from lamson.server import Relay
from config.settings import *

from lamson_subclass import MurmurMailResponse


'''
MailX Mail Utils and Constants

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''

HOST = 'murmur\.csail\.mit\.edu|mailx\.csail\.mit\.edu'
NO_REPLY = 'no-reply' + '@murmur.csail.mit.edu'
POST_SUFFIX = '__post__'
FOLLOW_SUFFIX = '__follow__'
UNFOLLOW_SUFFIX = '__unfollow__'
UPVOTE_SUFFIX = '__upvote__'
DOWNVOTE_SUFFIX = '__downvote__'
FETCH_SUFFIX = '__fetch__'

RESERVED = ['+create', '+activate', '+deactivate', '+subscribe', '+unsubscribe', '+info', 'help', 'no-reply', 'all', POST_SUFFIX, FOLLOW_SUFFIX, UNFOLLOW_SUFFIX, UPVOTE_SUFFIX, DOWNVOTE_SUFFIX, FETCH_SUFFIX]

relay_mailer = Relay(host=relay_config['host'], port=relay_config['port'], debug=1)

ALLOWED_MIMETYPES = ["image/jpeg", "image/bmp", "image/gif", "image/png", "application/pdf"]
MAX_ATTACHMENT_SIZE = 1000000

def setup_post(From, Subject, group_name):
	
	host = 'murmur.csail.mit.edu'
	
	post_addr = '%s <%s>' %(group_name, group_name + '@' + host)

	mail = MurmurMailResponse(From = From, 
						To = post_addr, 
						Subject = Subject)

	mail.update({
		"Sender": post_addr, 
		"Reply-To": post_addr,
		"List-Id": post_addr,
		"List-Unsubscribe": "<mailto:%s+unsubscribe@%s>" % (group_name,host),
		"List-Archive": "<http://%s/groups/%s/>" % (host, group_name),
		"List-Post": "<mailto:%s>" % (group_name + '@' + host),
		"List-Help": "<mailto:help@%s>" % host,
		"List-Subscribe": "<mailto:%s+subscribe@%s>" % (group_name,host),
		"Return-Path": post_addr, 
		"Precedence": 'list',
	})
	
	return mail


def create_error_email(addr, group_name, host, error):
	mail = setup_post(NO_REPLY, addr, "Error", group_name, host)
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
					body = re.sub(r'<div style="border-top:solid thin;padding-top:5px;margin-top:10px"><a href="mailto:.*?\+__follow__@murmur\.csail\.mit\.edu" target="_blank">Follow<\/a> \| <a href="mailto:.*?\+__unfollow__@mailx\.csail\.mit\.edu" target="_blank">Un-Follow<\/a><\/div>','',body)
					res['html'] += body
				else:
					body = part.get_payload()
					body = re.sub(r'Follow <.*?\+__follow__@murmur\.csail\.mit\.edu> \| Un-Follow\\n> <.*?\+__unfollow__@murmur.csail\.mit\.edu>','', body)
					res['plain'] += body
			elif part.get_content_maintype() == 'multipart':
				for part2 in part.get_payload():
					if part2.get_content_subtype() == 'html':
						body = part2.get_payload()
						body = re.sub(r'<div style="border-top:solid thin;padding-top:5px;margin-top:10px"><a href="mailto:.*?\+__follow__@murmur\.csail\.mit\.edu" target="_blank">Follow<\/a> \| <a href="mailto:.*?\+__unfollow__@mailx\.csail\.mit\.edu" target="_blank">Un-Follow<\/a><\/div>','',body)
						res['html'] += body
					elif part2.get_content_subtype() == 'plain':
						body = part2.get_payload()
						body = re.sub(r'Follow <.*?\+__follow__@murmur\.csail\.mit\.edu> \| Un-Follow\\n> <.*?\+__unfollow__@murmur.csail\.mit\.edu>','', body)
						res['plain'] += body
	elif maintype == 'text':
		if subtype == 'html':
			body = email_message.get_payload()
			body = re.sub(r'<div style="border-top:solid thin;padding-top:5px;margin-top:10px"><a href="mailto:.*?\+__follow__@murmur\.csail\.mit\.edu" target="_blank">Follow<\/a> \| <a href="mailto:.*?\+__unfollow__@mailx\.csail\.mit\.edu" target="_blank">Un-Follow<\/a><\/div>','',body)
			res['html'] = body
		elif subtype == 'text':
			body = email_message.get_payload()
			body = re.sub(r'Follow <.*?\+__follow__@murmur\.csail\.mit\.edu> \| Un-Follow\\n> <.*?\+__unfollow__@murmur.csail\.mit\.edu>','', body)
			res['plain'] = body
	return res

def html_ps(group_name):
	host = 'murmur.csail.mit.edu'
	follow_addr = 'mailto:%s' %(group_name + '+' + FOLLOW_SUFFIX + '@' + host)
	unfollow_addr = 'mailto:%s' %(group_name + '+'  + UNFOLLOW_SUFFIX + '@' + host)
	content = '<a href="%s">Follow</a> | <a href="%s">Un-Follow</a>' %(follow_addr, unfollow_addr)
	body = '<div style="border-top:solid thin; padding-top:5px; margin-top:10px;">%s</div>' %(content)
	return body

def plain_ps(group_name):
	host = 'murmur.csail.mit.edu'
	follow_addr = 'mailto:%s' %(group_name + '+' + FOLLOW_SUFFIX + '@' + host)
	unfollow_addr = 'mailto:%s' %(group_name + '+'  + UNFOLLOW_SUFFIX + '@' + host)
	content = 'Follow<%s> | Un-Follow<%s>' %(follow_addr, unfollow_addr)
	return content
