import email, re
from lamson.mail import MailResponse
from lamson.server import Relay
from config.settings import *


'''
MailX Mail Utils and Constants

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''

HOST = 'mailx.csail.mit.edu'
NO_REPLY = 'no-reply' + '@' + HOST
POST_SUFFIX = '__post__'
FOLLOW_SUFFIX = '__follow__'
UNFOLLOW_SUFFIX = '__unfollow__'
UPVOTE_SUFFIX = '__upvote__'
DOWNVOTE_SUFFIX = '__downvote__'
FETCH_SUFFIX = '__fetch__'

RESERVED = ['+create', '+activate', '+deactivate', '+subscribe', '+unsubscribe', '+info', 'help', 'no-reply', 'all', POST_SUFFIX, FOLLOW_SUFFIX, UNFOLLOW_SUFFIX, UPVOTE_SUFFIX, DOWNVOTE_SUFFIX, FETCH_SUFFIX]

relay_mailer = Relay(host=relay_config['host'], port=relay_config['port'], debug=1)


def get_body(message):
	res = {}
	email_message = email.message_from_string(str(message))
	maintype = email_message.get_content_maintype()
	subtype = email_message.get_content_maintype()

	if maintype == 'multipart':
		for part in email_message.get_payload():
			if part.get_content_maintype() == 'text':
				if part.get_content_subtype() == 'html':
					body = part.get_payload()
					body = re.sub(r'<div style="border-top:solid thin;padding-top:5px;margin-top:10px"><a href="mailto:.*?\+__follow__@mailx\.csail\.mit\.edu" target="_blank">Follow<\/a> \| <a href="mailto:.*?\+__unfollow__@mailx\.csail\.mit\.edu" target="_blank">Un-Follow<\/a><\/div>','',body)
					res['html'] = body
				else:
					body = part.get_payload()
					body = re.sub(r'Follow <.*?\+__follow__@mailx\.csail\.mit\.edu> \| Un-Follow\\n> <.*?\+__unfollow__@mailx.csail\.mit\.edu>','', body)
					res['plain'] = body
	elif maintype == 'text':
		if subtype == 'html':
			body = email_message.get_payload()
			body = re.sub(r'<div style="border-top:solid thin;padding-top:5px;margin-top:10px"><a href="mailto:.*?\+__follow__@mailx\.csail\.mit\.edu" target="_blank">Follow<\/a> \| <a href="mailto:.*?\+__unfollow__@mailx\.csail\.mit\.edu" target="_blank">Un-Follow<\/a><\/div>','',body)
			res['html'] = body
		elif subtype == 'text':
			body = email_message.get_payload()
			body = re.sub(r'Follow <.*?\+__follow__@mailx\.csail\.mit\.edu> \| Un-Follow\\n> <.*?\+__unfollow__@mailx.csail\.mit\.edu>','', body)
			res['plain'] = body
	return res

	
def html_ps(group_name, host):
	follow_addr = 'mailto:%s' %(group_name + '+' + FOLLOW_SUFFIX + '@' + host)
	unfollow_addr = 'mailto:%s' %(group_name + '+'  + UNFOLLOW_SUFFIX + '@' + host)
	content = '<a href="%s">Follow</a> | <a href="%s">Un-Follow</a>' %(follow_addr, unfollow_addr)
	body = '<div style="border-top:solid thin; padding-top:5px; margin-top:10px;">%s</div>' %(content)
	return body

def plain_ps(group_name, host):
	follow_addr = 'mailto:%s' %(group_name + '+' + FOLLOW_SUFFIX + '@' + host)
	unfollow_addr = 'mailto:%s' %(group_name + '+'  + UNFOLLOW_SUFFIX + '@' + host)
	content = 'Follow<%s> | Un-Follow<%s>' %(follow_addr, unfollow_addr)
	return content
