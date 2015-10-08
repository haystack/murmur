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
	if '+' in address and '__' in address:
		return
	
	try:
	
		#does this fix the MySQL has gone away erro?
		django.db.close_connection()
		
		address = address.lower()
		name, addr = parseaddr(message['From'].lower())
		reserved = filter(lambda x: address.endswith(x), RESERVED)
		if(reserved):
			return
		
		group_name = address.lower()
		try:
			group = Group.objects.get(name=group_name)
		except Exception, e:
			mail = create_error_email(addr, group_name, host, e)
			relay.deliver(mail)
			return
		
		if message['Subject'][0:4] != "Re: ":
			orig_message = message['Subject']
		else:
			orig_message = re.sub("\[.*?\]", "", message['Subject'])
		
		email_message = email.message_from_string(str(message))
		msg_text = get_body(email_message)
	
		attachments = get_attachments(email_message)
		if len(attachments['attachments']) > 0:
			if not group.allow_attachments:
				mail = create_error_email(addr, group_name, host, "No attachments allowed for this group.")
				relay.deliver(mail)
				return
			
		if attachments['error'] != '':
			mail = create_error_email(addr, group_name, host, attachments['error'])
			relay.deliver(mail)
			return
	
		if message['Subject'][0:4] == "Re: ":
			if 'html' in msg_text:
				msg_text['html'] = re.sub('(?s)<div style="border-top:solid thin;padding-top:5px;margin-top:10px">.*?</div>','', msg_text['html'])
			if 'plain' in msg_text:
				msg_text['plain'] = re.sub('(?s)\n>  Follow <test\+__follow__@murmur.csail.mit.edu> \| Un-Follow\n> <test\+__unfollow__@murmur.csail.mit.edu>\n', '', msg_text['plain'])
		
		if 'html' not in msg_text:
			msg_text['html'] = markdown(msg_text['plain'])
		if 'plain' not in msg_text:
			msg_text['plain'] = html2text(msg_text['html'])
		
		
		user = UserProfile.objects.get(email=addr)
		
		if message['Subject'][0:4] == "Re: ":
			res = insert_reply(group_name, orig_message, msg_text['html'], user)
		else:
			res = insert_post(group_name, orig_message, msg_text['html'], user)
			
		if(not res['status']):
			mail = create_error_email(addr, group_name, host, res['code'])
			relay.deliver(mail)
			return
	
		if message['Subject'][0:4] != "Re: ":
			subj_tag = ''
			for tag in res['tags']:
				subj_tag += '[%s]' % tag
				
			subject = '[%s]%s %s' %(group_name, subj_tag,message['Subject'])
		else:
			subject = message['Subject']
			
		mail = setup_post(message['From'],
							subject,	
							group_name)
			
		for attachment in attachments.get("attachments"):
			mail.attach(filename=attachment['filename'],
						content_type=attachment['mime'],
						data=attachment['content'],
						disposition=attachment['disposition'],
						id=attachment['id'])
			
		if 'references' in message:
			mail['References'] = message['references']
		elif 'message-id' in message:
			mail['References'] = message['message-id']	
			
	
		if 'in-reply-to' not in message:
			mail["In-Reply-To"] = message['message-id']
		
		msg_id = res['msg_id']
		to_send =  res['recipients']
		
		mail['message-id'] = msg_id
			
		logging.debug('TO LIST: ' + str(to_send))
		
		g = Group.objects.get(name=group_name)
		t = Thread.objects.get(id=res['thread_id'])
		
		if len(to_send) > 0:
			for recip_email in to_send:
				recip = UserProfile.objects.get(email=recip_email)
				membergroup = MemberGroup.objects.get(group=g, member=recip)
				
				following = Following.objects.filter(thread=t, user=recip).exists()
				muting = Mute.objects.filter(thread=t, user=recip).exists()
			
				ps_blurb = html_ps(g, t, membergroup, following, muting)
				
				try:
					mail.Html = unicode(msg_text['html'] + ps_blurb)	
				except UnicodeDecodeError:
					mail.Html = unicode(msg_text['html'] + ps_blurb, "utf-8")
				
				ps_blurb = plain_ps(g, t, membergroup, following, muting)
				try:
					mail.Body = unicode(msg_text['plain'] + ps_blurb)
				except UnicodeDecodeError:
					mail.Body = unicode(msg_text['plain'] + ps_blurb, "utf-8")
			
				relay.deliver(mail, To = recip_email)
	except Exception, e:
		logging.debug(e)
		mail = create_error_email(addr, group_name, host, e)
		relay.deliver(mail)
		return
	
		
		


@route("(group_name)\\+(thread_id)(suffix)@(host)", group_name=".+", thread_id=".+", suffix=FOLLOW_SUFFIX+"|"+FOLLOW_SUFFIX.upper(), host=HOST)
@stateless
def handle_follow(message, group_name=None, thread_id=None, suffix=None, host=None):
	name, addr = parseaddr(message['From'].lower())
	res = follow_thread(thread_id, email=addr)
	if(res['status']):
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = res['thread_name'], Body = "Success! You are now following the thread \"%s\". You will receive emails for all following replies to to this thread." % res['thread_name'])
		relay.deliver(mail)
	else:
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = res['thread_name'], Body = "Sorry there was an error: %s" % (res['code']))
		relay.deliver(mail)
	return





@route("(group_name)\\+(thread_id)(suffix)@(host)", group_name=".+", thread_id=".+", suffix=UNFOLLOW_SUFFIX+"|"+UNFOLLOW_SUFFIX.upper(), host=HOST)
@stateless
def handle_unfollow(message, group_name=None, thread_id=None, suffix=None, host=None):
	name, addr = parseaddr(message['From'].lower())
	res = unfollow_thread(thread_id, email=addr)
	if(res['status']):
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = res['thread_name'], Body = "You unfollowed the thread \"%s\" successfully." % res['thread_name'])
		relay.deliver(mail)
	else:
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = res['thread_name'], Body = "Error Message: %s" %(res['code']))
		relay.deliver(mail)
	return


@route("(group_name)\\+(thread_id)(suffix)@(host)", group_name=".+", thread_id=".+", suffix=MUTE_SUFFIX+"|"+MUTE_SUFFIX.upper(), host=HOST)
@stateless
def handle_mute(message, group_name=None, thread_id=None, suffix=None, host=None):
	name, addr = parseaddr(message['From'].lower())
	res = mute_thread(thread_id, email=addr)
	if(res['status']):
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = res['thread_name'], Body = "Success! You have now muted the thread \"%s\"." % res['thread_name'])
		relay.deliver(mail)
	else:
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = res['thread_name'], Body = "Sorry there was an error: %s" % (res['code']))
		relay.deliver(mail)
	return





@route("(group_name)\\+(thread_id)(suffix)@(host)", group_name=".+", thread_id=".+", suffix=UNMUTE_SUFFIX+"|"+UNMUTE_SUFFIX.upper(), host=HOST)
@stateless
def handle_unmute(message, group_name=None, thread_id=None, suffix=None, host=None):
	name, addr = parseaddr(message['From'].lower())
	res = unmute_thread(thread_id, email=addr)
	if(res['status']):
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = res['thread_name'], Body = "You unmuted the thread \"%s\" successfully. You will receive emails for all following replies to to this thread." % res['thread_name'])
		relay.deliver(mail)
	else:
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = res['thread_name'], Body = "Error Message: %s" %(res['code']))
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
