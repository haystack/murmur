import logging, time, base64
from lamson.routing import route, stateless
from config.settings import relay
from schema.models import *
from lamson.mail import MailResponse
from email.utils import *
from engine.main import *
from utils import *
from html2text import html2text
from markdown2 import markdown
from django.db.utils import OperationalError
import django.db

'''
MailX Mail Interface Handler

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
	
	if message['Subject'][0:4] != "Re: ":
		subject = '[ %s ] %s' %(group_name, message['Subject'])
	else:
		subject = message['Subject']
	
	email_message = email.message_from_string(str(message))
	msg_text = get_body(email_message)
	
	if message['Subject'][0:4] == "Re: ":
		if 'html' in msg_text:
			msg_text['html'] = re.sub('(?s)<div style="border-top:solid thin;padding-top:5px;margin-top:10px">.*?</div>','', msg_text['html'])
		if 'plain' in msg_text:
			msg_text['plain'] = re.sub('(?s)\n>  Follow <test\+__follow__@murmur.csail.mit.edu> \| Un-Follow\n> <test\+__unfollow__@murmur.csail.mit.edu>\n', '', msg_text['plain'])
	
	if 'html' not in msg_text:
		msg_text['html'] = markdown(msg_text['plain'])
	if 'plain' not in msg_text:
		msg_text['plain'] = html2text(msg_text['html'])
	
	try:
		user = UserProfile.objects.get(email=addr)
	except OperationalError:
		django.db.close_connection()
		user = UserProfile.objects.get(email=addr)
	
	if message['Subject'][0:4] == "Re: ":
		res = insert_reply(group_name, message['Subject'], msg_text['html'], user)
	else:
		res = insert_post(group_name, subject, msg_text['html'], user)
		
	if(not res['status']):
		mail = setup_post(NO_REPLY, addr, "Error", group_name, host)
		mail.Body = "Error Message:%s" %(res['code'])
		
		relay.deliver(mail)
		return
	
	post_addr = '%s <%s>' %(group_name, group_name + '@' + host)
	
	mail = setup_post(message['From'], 
						post_addr, 
						subject,	
						group_name, 
						host)
		
	if 'references' in message:
		mail['References'] = message['references']
	elif 'message-id' in message:
		mail['References'] = message['message-id']	
		

	if 'in-reply-to' not in message:
		mail["In-Reply-To"] = message['message-id']
	
	
	if len(email_message.get_payload()) > 1:
		attachments = get_attachments(email_message)
		for attachment in attachments.get("attachments"):
			mail.attach(filename=attachment['filename'],
						content_type=attachment['mime'],
						data=attachment['content'])
	
	msg_id = res['msg_id']
	to_send =  res['recipients']
	
	mail['message-id'] = msg_id

	ps_blurb = html_ps(group_name, host)
	
	try:
		mail.Html = unicode(msg_text['html'] + ps_blurb)	
	except UnicodeDecodeError:
		mail.Html = unicode(msg_text['html'] + ps_blurb, "utf-8")
	
	ps_blurb = plain_ps(group_name, host)
	try:
		mail.Body = unicode(msg_text['plain'] + ps_blurb)
	except UnicodeDecodeError:
		mail.Body = unicode(msg_text['plain'] + ps_blurb, "utf-8")
		
	logging.debug('TO LIST: ' + str(to_send))
	
	if(len(to_send)>0):
		relay.deliver(mail, To = to_send)



@route("(group_name)\\+(thread_id)\\+(msg_id)(suffix)@(host)", group_name=".+", thread_id=".+", msg_id=".+", suffix=FOLLOW_SUFFIX+"|"+FOLLOW_SUFFIX.upper(), host=HOST)
@stateless
def handle_follow(message, group_name=None, thread_id=None, msg_id=None, suffix=None, host=None):
	name, addr = parseaddr(message['From'].lower())
	msg_id = msg_id.lower()
	res = follow_thread(thread_id, addr)
	if(res['status']):
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = "Success", Body = "Follow success.")
		relay.deliver(mail)
	else:
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = "Error", Body = "Error Message: %s" %(res['code']))
		relay.deliver(mail)
	return





@route("(group_name)\\+(thread_id)\\+(msg_id)(suffix)@(host)", group_name=".+", thread_id=".+", msg_id=".+", suffix=UNFOLLOW_SUFFIX+"|"+UNFOLLOW_SUFFIX.upper(), host=HOST)
@stateless
def handle_unfollow(message, group_name=None, thread_id=None, msg_id=None, suffix=None, host=None):
	name, addr = parseaddr(message['From'].lower())
	msg_id = msg_id.lower()
	res = unfollow_thread(thread_id, addr)
	if(res['status']):
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = "Success", Body = "Unfollow success")
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


@route("(address)@(host)", address=".+", host=".+")
@stateless
def send_account_info(message, address=None, host=None):
	if str(message['From']) == "no-reply@murmur.csail.mit.com" and ("Account activation on Murmur" in str(message['Subject']) or "Password reset on Murmur" in str(message['Subject'])):
		logging.debug(message['Subject'])
		logging.debug(message['To'])
		logging.debug(message['From'])
		
		email_message = email.message_from_string(str(message))
		msg_text = get_body(email_message)
		mail = MailResponse(From = NO_REPLY, To = message['To'], Subject = message['Subject'], Body = msg_text['plain'])
		relay.deliver(mail)
