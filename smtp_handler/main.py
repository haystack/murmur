import logging, time, base64, email, re
from lamson.routing import route, stateless
from config.settings import relay
from schema.models import *
from email.utils import *
from lamson.mail import MailResponse
from engine.main import *

'''
MailX Mail Interface Handler

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''

HOST = 'slow.csail.mit.edu'
NO_REPLY = 'no-reply' + '@' + HOST
POST_SUFFIX = '__post__'
FOLLOW_SUFFIX = '__follow__'
UNFOLLOW_SUFFIX = '__unfollow__'
UPVOTE_SUFFIX = '__upvote__'
DOWNVOTE_SUFFIX = '__downvote__'
FETCH_SUFFIX = '__fetch__'

RESERVED = ['+create', '+activate', '+deactivate', '+subscribe', '+unsubscribe', '+info', 'help', 'no-reply', 'all', POST_SUFFIX, FOLLOW_SUFFIX, UNFOLLOW_SUFFIX, UPVOTE_SUFFIX, DOWNVOTE_SUFFIX, FETCH_SUFFIX]




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





@route("(group_name)\\+subscribe@(host)", group_name=".+", host=HOST)
@stateless
def subscribe(message, group_name=None, host=None):
	group = None
	group_name = group_name.lower()
	name, addr = parseaddr(message['from'].lower())
	res = subscribe_group(group_name, addr)
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
	res = unsubscribe_group(group_name, addr)
	subject = "Un-subscribe -- Success"
	body = "You are now un-subscribed from: %s@%s" %(group_name, host)
	if(not res['status']):
		subject = "Un-subscribe -- Error"
		body = "Error Message: %s" %(res['code'])
	mail = MailResponse(From = NO_REPLY, To = message['From'], Subject = subject, Body = body)
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
	address = address.lower()
	name, addr = parseaddr(message['From'].lower())
	reserved = filter(lambda x: address.endswith(x), RESERVED)
	if(reserved):
		return
	group_name = address.lower()
	msg_text = get_body(str(message))
	res = insert_post(group_name, message['Subject'], msg_text['body'], addr)
	if(not res['status']):
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = "Error", Body = "Error Message:%s" %(res['code']))
		relay.deliver(mail)
		return
	id = res['id']
	to_send =  res['recipients']
	post_addr = '%s <%s>' %(group_name, group_name + '+' + id + POST_SUFFIX + '@' + host)
	mail = MailResponse(From = message['From'], To = post_addr, Subject  = '[ %s ] -- %s' %(group_name, message['Subject']))
	msg_id = message['message-id']
		
	if 'references' in message:
		mail['References'] = message['References']
	elif msg_id:
		mail['References'] = msg_id

	if msg_id:
		mail['message-id'] = msg_id	
	
	ps_blurb = html_ps(id, group_name, host)
	mail.Html = unicode(msg_text['body'] + ps_blurb , "utf-8")		
	logging.debug('TO LIST: ' + str(to_send))
	relay.deliver(mail, To = to_send)






@route("(group_name)\\+(post_id)(suffix)@(host)", group_name=".+", post_id=".+", suffix=POST_SUFFIX+"|"+POST_SUFFIX.upper(), host=HOST)
@stateless
def handle_reply(message, group_name=None, post_id=None, suffix=None, host=None):
	name, addr = parseaddr(message['from'].lower())
	post_id = post_id.lower()
	group_name = group_name.lower()
	msg_text = get_body(str(message))
	res = insert_reply(group_name, message['Subject'], msg_text['body'], addr, post_id)
	if(not res['status']):
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = "Error", Body = "Error Message:%s" %(res['code']))
		relay.deliver(mail)
		return
	id = res['id']
	to_send =  res['recipients']
	mail = MailResponse(From = message['From'], To = message['To'], Subject = message['Subject'])
	msg_id = message['message-id']
	if 'references' in message:
		mail['References'] = message['References']
	elif msg_id:
		mail['References'] = msg_id

	if msg_id:
		mail['message-id'] = msg_id
	
	ps_blurb = html_ps(id, group_name, host)
	mail.Html = unicode(msg_text['body'] + ps_blurb , "utf-8")
	logging.debug('TO LIST: ' + str(to_send))
	relay.deliver(mail, To = to_send)




@route("(group_name)\\+(post_id)(suffix)@(host)", group_name=".+", post_id=".+", suffix=FOLLOW_SUFFIX+"|"+FOLLOW_SUFFIX.upper(), host=HOST)
@stateless
def handle_follow(message, group_name=None, post_id=None, suffix=None, host=None):
	name, addr = parseaddr(message['From'].lower())
	post_id = post_id.lower()
	res = follow_post(post_id, addr)
	if(res['status']):
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = "Success", Body = "Follow success (post:%s)" %(post_id))
		relay.deliver(mail)
	else:
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = "Error", Body = "Error Message: %s" %(res['code']))
		relay.deliver(mail)
	return





@route("(group_name)\\+(post_id)(suffix)@(host)", group_name=".+", post_id=".+", suffix=UNFOLLOW_SUFFIX+"|"+UNFOLLOW_SUFFIX.upper(), host=HOST)
@stateless
def handle_unfollow(message, group_name=None, post_id=None, suffix=None, host=None):
	name, addr = parseaddr(message['From'].lower())
	post_id = post_id.lower()
	res = unfollow_post(post_id, addr)
	if(res['status']):
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = "Success", Body = "Unfollow success (post:%s)" %(post_id))
		relay.deliver(mail)
	else:
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = "Error", Body = "Error Message: %s" %(res['code']))
		relay.deliver(mail)
	return



"""

@route("(post_id)(suffix)@(host)", post_id=".+", suffix=UPVOTE_SUFFIX+"|"+UPVOTE_SUFFIX.upper(), host=HOST)
@stateless
def handle_upvote(message, post_id=None, suffix=None, host=None):
	name, addr = parseaddr(message['from'].lower())
	post_id = post_id.lower()
	mail = None
	post = None
        try:
                post = Post.objects.get(id=post_id)
		f = Like.objects.get(post = post, email=addr)
	except Likes.DoesNotExist:
		like = Like(post = post, email = addr)
		like.save()
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = "Success", Body = "Upvoted the  post:%s" %(post_id))
                relay.deliver(mail)  
        except Post.DoesNotExist:
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = "Error", Body = "Invalid post:%s" %(post_id))
        	relay.deliver(mail)
	return




@route("(post_id)(suffix)@(host)", post_id=".+", suffix=DOWNVOTE_SUFFIX+"|"+DOWNVOTE_SUFFIX.upper(), host=HOST)
@stateless
def handle_downvote(message, post_id=None, suffix=None, host=None):
	name, addr = parseaddr(message['from'].lower())
	post_id = post_id.lower()
	mail = None
	post = None
        try:
                post = Post.objects.get(id=post_id)
                dislike = Dislike.objects.get(post = post, email=addr)
		like = Like.objects.get(post = post, email=addr)
		like.delete()
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = "Success", Body = "Downvoted the post:%s" %(post_id))
                relay.deliver(mail)
	except Dislike.DoesNotExist:
		dislike = Disike(post = post, email = addr)
                dislike.save()
        	mail = MailResponse(From = NO_REPLY, To = addr, Subject = "Success", Body = "Downvoted the post:%s" %(post_id))
                relay.deliver(mail)
	except Post.DoesNotExist:
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = "Error", Body = "Invalid post:%s" %(post_id))
        	relay.deliver(mail)
	return

"""



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


def get_body(message):
	res={}
	email_message = email.message_from_string(str(message))
	maintype = email_message.get_content_maintype()
	subtype = email_message.get_content_maintype()
	body = None
	if maintype == 'multipart':
		for part in email_message.get_payload():
			if part.get_content_maintype() == 'text':
				if part.get_content_subtype() == 'html':
					res['type']='html'
					body = part.get_payload()
					break
				else:
					res['type']='plain'
					res['body']=part.get_payload()
	elif maintype == 'text':
		if subtype == 'html':
			res['type']='html'
			body =email_message.get_payload()
		elif subtype == 'text':
			res['type']='plain'
			body =email_message.get_payload()
	body = re.sub(r'<div.*?<a.*?\_\_follow\_\_.*?a>.*?<a.*?\_\_unfollow\_\_.*?a>.*?div>', '', body)
	res['body'] = body
	return res
	
def html_ps(id, group_name, host):
	follow_addr = 'mailto:%s' %(group_name + '+' + id + FOLLOW_SUFFIX + '@' + host)
	unfollow_addr = 'mailto:%s' %(group_name + '+' + id + UNFOLLOW_SUFFIX + '@' + host)
	content = '<a href="%s">Follow</a> | <a href="%s">Un-Follow</a>' %(follow_addr, unfollow_addr)
	body = '<div style="border-top:solid thin; padding-top:5px;">%s</div>' %(content)
	return body
