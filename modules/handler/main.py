import logging, time, base64
from lamson.routing import route, stateless
from config.settings import relay
from models import *
from email.utils import *
from lamson.mail import MailResponse

'''
Slow_Email Main Handler

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''

HOST = 'slow.csail.mit.edu'
NO_REPLY = 'no-reply' + '@' + HOST
SUFFIX = '__post__'
RESERVED = ['-create', '-activate', '-deactivate', '-subscribe', '-unsubscribe', '-info', 'help', 'no-reply', SUFFIX]

@route("(group_name)-create@(host)", group_name=".+", host=HOST)
@stateless
def create(message, group_name=None, host=None):
	group_name = group_name.lower()
	name, addr = parseaddr(message['from'].lower())
	subject = "Create Group -- Success"
	body = "Mailing group %s@%s created" %(group_name, host)
	try:
		group = Group.objects.get(name=group_name)
		subject = "Create Group -- Error"
		body = "Mailing group %s@%s already exists" %(group_name, host)
	except Group.DoesNotExist:
		group = Group(name=group_name, status=True)
		group.save()
		user = User(email = addr, group = group, admin = True, status = True)
        	user.save()
	
	mail = MailResponse(From = NO_REPLY, To = message['From'], Subject = subject, Body = body)
	relay.deliver(mail)
        return


@route("(group_name)-activate@(host)", group_name=".+", host=HOST)
@stateless
def activate(message, group_name=None, host=None):
	group = None
	group_name = group_name.lower()
	subject = "Activate Group -- Success"
	body = "Activated: %s@%s" %(group_name, host))
	name, addr = parseaddr(message['from'].lower())
	try:                    
                group = Group.objects.get(name=group_name)
		user = User.objects.get(email = addr, group = group, admin = True)
		group.status = True
		group.save()
	except User.DoesNotExist:
		subject = "Activate Group -- Error"
		body = "You do not have the privilege to activate: %s@%s" %(group_name, host)
        except Group.DoesNotExist:
       	 	subject =  "Activate Group -- Error"
		body = "Could not locate %s@%s group" %(group_name, host)
        
	mail = MailResponse(From = NO_REPLY, To = message['From'], Subject = subject, Body = body) 
        relay.deliver(mail)
	return


@route("(group_name)-deactivate@(host)", group_name=".+", host=HOST)
@stateless
def deactivate(message, group_name=None, host=None):
	group = None
	group_name = group_name.lower()
	subject = "De-activate Group -- Success"
        body = "De-activated: %s@%s" %(group_name, host)
	name, addr = parseaddr(message['from'].lower())
	try:                    
                group = Group.objects.get(name=group_name)
		user = User.objects.get(email = addr, group = group, admin = True)
		group.status = False
		group.save()
	except User.DoesNotExist:
		subject = "De-activate Group -- Error"
                body = "You do not have the privilege to de-activate: %s@%s" %(group_name, host)
        except Group.DoesNotExist:
		subject = "De-activate Group -- Error"
                body = "You do not have the privilege to de-activate: %s@%s" %(group_name, host)
        
	mail = MailResponse(From = NO_REPLY, To = message['From'], Subject = subject, Body = body) 
        relay.deliver(mail)
	return



@route("(group_name)-subscribe@(host)", group_name=".+", host=HOST)
@stateless
def subscribe(message, group_name=None, host=None):
	group = None
	group_name = group_name.lower()
	subject = "Subscribe -- Success"
	body = "You are now subscribed to: %s@%s" %(group_name, host)
	name, addr = parseaddr(message['from'].lower())
	try:                    
                group = Group.objects.get(name=group_name, status = True)
		user = User.objects.get(email = addr, group = group)
		subject = "Subscribe -- Error"
		body = "You are already subscribed to: %s@%s" %(group_name, host)
	except User.DoesNotExist:
                user = User(email = addr, group = group, admin = False, status = True)
		user.save()
        except Group.DoesNotExist:
       	 	subject = "Subscribe -- Error"
		body = "Could not locate the group: %s@%s" %(group_name, host)
        
	mail = MailResponse(From = NO_REPLY, To = message['From'], Subject = subject, Body = body) 
        relay.deliver(mail)
	return


@route("(group_name)-unsubscribe@(host)", group_name=".+", host=HOST)
@stateless
def unsubscribe(message, group_name=None, host=None):
	group = None
	group_name = group_name.lower()
	subject = "Un-subscribe -- Success"
        body = "You are now un-subscribed from: %s@%s" %(group_name, host)
	name, addr = parseaddr(message['from'].lower())
	try:                    
                group = Group.objects.get(name=group_name, status = True)
		user = User.objects.get(email = addr, group = group)
		if(user.admin):
			subject = "Un-subscribe Error"
			body = "Can't un-subscribe the group owner from: %s@%s" %(group_name, host)
		else:
			user.delete()
	except User.DoesNotExist:
		subject = "Un-subscribe -- Error"
                body = "You are not subscribed to: %s@%s" %(group_name, host)
        except Group.DoesNotExist:
		subject = "Un-subscribe -- Error"
                body = "Could not locate the group: %s@%s" %(group_name, host)
        
	mail = MailResponse(From = NO_REPLY, To = message['From'], Subject = subject, Body = body) 
        relay.deliver(mail)
	return


@route("(group_name)-info@(host)", group_name=".+", host=HOST)
@stateless
def info(message, group_name=None, host=None):
	group_name = group_name.lower()
	subject = "Group Info -- Success"
	body = ""
        try:
                group = Group.objects.get(name=group_name)
		members = User.objects.filter(group=group).values()
                body = "Group Name: %s@%s, Status: %s, Members: %s" %(group_name, host, group.status, str(members))
        except Group.DoesNotExist:
		subject = "Group Info -- Error"
		body = "Could not locate the group: %s@%s" %(group_name, host)
        
	mail = MailResponse(From = NO_REPLY, To = message['From'], Subject = subject, Body = body) 
        relay.deliver(mail)
	return


@route("(address)@(host)", address=".+", host=HOST)
@stateless
def handle_post(message, address=None, host=None):
	address = address.lower()
	name, addr = parseaddr(message['from'].lower())
	reserved = filter(lambda x: address.endswith(x), RESERVED)
	if(reserved):
		return
	group_name = address
	group = None
	mail = None
	try:
		group = Group.objects.get(name=group_name)
		id = base64.b64encode(addr+str(time.time())).lower()
		p = Post(id = id, from_email = addr, subject = message['Subject'], message=str(message))
		p.save()
		post_addr = '%s <%s>' %(addr, id + SUFFIX + '@' + HOST)
		mail = MailResponse(From = post_addr, To = addr, Subject  = '[ %s ] -- %s' %(group_name, message['Subject']))
		if message.all_parts():
        		mail.attach_all_parts(message)
    		else:
        		mail.Body = message.body()
		relay.deliver(mail)
	except Group.DoesNotExist:
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = "Error", Body = "Invalid address: %s@%s" %(group_name, host))
        
	relay.deliver(mail)
	return


@route("(post_id)(suffix)@(host)", post_id=".+", suffix=SUFFIX+"|"+SUFFIX.upper(), host=HOST)
@stateless
def handle_reply(message, post_id=None, suffix=None, host=None):
	name, addr = parseaddr(message['from'].lower())
	post_id = post_id.lower()
	mail = None
        try:
                post = Post.objects.get(id=post_id)
		r = Reply(from_email = addr, message = post, reply = str(message))
		r.save()
		mail = MailResponse(From = '%s <%s>' %(addr, post_id + SUFFIX + '@' + HOST), To = addr, Subject = message['Subject'])
		if message.all_parts():
                        mail.attach_all_parts(message)
                else:
                        mail.Body = message.body()
        except Post.DoesNotExist:
		mail = MailResponse(From = NO_REPLY, To = addr, Subject = "Error", Body = "Invalid post:%s" %(post_id))
        
	relay.deliver(mail)
	return




@route("(address)@(host)", address="help", host=HOST)
@stateless
def help(message, address=None, host=None):
	to_addr = message['From']
	from_addr = address + '@' + HOST
	subject = "Help"
	body = "For creating a new post, simply send an email to the group email address. For replying to a post, reply to the from_address of the post (just hit the reply button in your email client). For administrative activities like creating, activating, deactivating, subscribing to, unsubscribing from, and viewing a group,  send an email to <group>-[create | activate | deactivate | subscribe | unsubscribe | info]@%s respectively." %(host) )
	mail = MailResponse(From = from_addr, To = to_addr, Subject = subject, Body = body)
	return


