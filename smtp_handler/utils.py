import email, re
from lamson.server import Relay
from config.settings import *

from lamson_subclass import MurmurMailResponse


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
UPVOTE_SUFFIX = '__upvote__'
DOWNVOTE_SUFFIX = '__downvote__'
FETCH_SUFFIX = '__fetch__'

FOLLOW_ADDR = 'http://%s/follow?tid=' % (HOST)
UNFOLLOW_ADDR = 'http://%s/unfollow?tid=' % (HOST)

HTML_SUBHEAD = '<div style="border-top:solid thin;padding-top:5px;margin-top:10px">'
HTML_SUBTAIL = '</div>'

PLAIN_SUBHEAD = '***\nMurmur\n'
PLAIN_SUBTAIL = '\n***\n'

RESERVED = ['+create', '+activate', '+deactivate', '+subscribe', '+unsubscribe', '+info', 'help', 'no-reply', 'all', POST_SUFFIX, FOLLOW_SUFFIX, UNFOLLOW_SUFFIX, UPVOTE_SUFFIX, DOWNVOTE_SUFFIX, FETCH_SUFFIX]

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

def html_ps(group_name, tid):
	#follow_addr = 'mailto:%s' %(group_name + '+' + FOLLOW_SUFFIX + '@' + HOST)
	#unfollow_addr = 'mailto:%s' %(group_name + '+'  + UNFOLLOW_SUFFIX + '@' + HOST)
	
	follow_addr = '%s%s' % (FOLLOW_ADDR, tid)
	unfollow_addr = '%s%s' % (UNFOLLOW_ADDR, tid)
	
	content = '<a href="%s">Follow</a> | <a href="%s">Un-Follow</a>' %(follow_addr, unfollow_addr)
	body = '%s%s%s' % (HTML_SUBHEAD, content, HTML_SUBTAIL)
	return body

def plain_ps(group_name, tid):
	follow_addr = 'mailto:%s' %(group_name + '+' + tid + FOLLOW_SUFFIX + '@' + HOST)
	unfollow_addr = 'mailto:%s' %(group_name + '+' + tid + UNFOLLOW_SUFFIX + '@' + HOST)
	
	content = 'Follow<%s> | Un-Follow<%s>' %(follow_addr, unfollow_addr)
	body = '%s%s%s' % (PLAIN_SUBHEAD, content, PLAIN_SUBTAIL)
	
	return body
