import logging, time, base64
from lamson.routing import route, stateless
from config.settings import relay
from models import *
from email.utils import *

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
	try:
		group = Group.objects.get(name=group_name)
		relay.reply(message, NO_REPLY, "Error", "Mailing group %s@%s already exists" %(group_name, host))
	except Group.DoesNotExist:
		group = Group(name=group_name, status=True)
		group.save()
		user = User(email = addr, group = group, admin = True, status = True)
        	user.save()
		relay.reply(message, NO_REPLY, "Success", "Mailing group %s@%s created" %(group_name, host))
        return


@route("(group_name)-activate@(host)", group_name=".+", host=HOST)
@stateless
def activate(message, group_name=None, host=None):
	group = None
	group_name = group_name.lower()
	name, addr = parseaddr(message['from'].lower())
	try:                    
                group = Group.objects.get(name=group_name)
		user = User.objects.get(email = addr, group = group, admin = True)
		group.status = True
		group.save()
		relay.reply(message, NO_REPLY, "Success", "Activated: %s@%s" %(group_name, host))
	except User.DoesNotExist:
		relay.reply(message, NO_REPLY, "Error", "You do not have the privilege to activate: %s@%s" %(group_name, host))
        except Group.DoesNotExist:
       	 	relay.reply(message, NO_REPLY, "Error", "Could not locate %s@%s group" %(group_name, host))
        return


@route("(group_name)-deactivate@(host)", group_name=".+", host=HOST)
@stateless
def deactivate(message, group_name=None, host=None):
	group = None
	group_name = group_name.lower()
	name, addr = parseaddr(message['from'].lower())
	try:                    
                group = Group.objects.get(name=group_name)
		user = User.objects.get(email = addr, group = group, admin = True)
		group.status = False
		group.save()
		relay.reply(message, NO_REPLY, "Success", "Deactivated: %s@%s" %(group_name, host))
	except User.DoesNotExist:
		relay.reply(message, NO_REPLY, "Error", "You do not have the privilege to deactivate: %s@%s" %(group_name, host))
        except Group.DoesNotExist:
       	 	relay.reply(message, NO_REPLY, "Error", "Could not locate %s@%s group" %(group_name, host))
        return



@route("(group_name)-subscribe@(host)", group_name=".+", host=HOST)
@stateless
def subscribe(message, group_name=None, host=None):
	group = None
	group_name = group_name.lower()
	name, addr = parseaddr(message['from'].lower())
	try:                    
                group = Group.objects.get(name=group_name, status = True)
		user = User.objects.get(email = addr, group = group)
		relay.reply(message, NO_REPLY, "Error", "You are already subscribed to: %s@%s" %(group_name, host))
	except User.DoesNotExist:
                user = User(email = addr, group = group, admin = False, status = True)
		user.save()
		relay.reply(message, NO_REPLY, "Success", "You are now subscribed to: %s@%s" %(group_name, host))
        except Group.DoesNotExist:
       	 	relay.reply(message, NO_REPLY, "Error", "Could not locate %s@%s group" %(group_name, host))
        return


@route("(group_name)-unsubscribe@(host)", group_name=".+", host=HOST)
@stateless
def unsubscribe(message, group_name=None, host=None):
	group = None
	group_name = group_name.lower()
	name, addr = parseaddr(message['from'].lower())
	try:                    
                group = Group.objects.get(name=group_name, status = True)
		user = User.objects.get(email = addr, group = group)
		if(user.admin):
			relay.reply(message, NO_REPLY, "Error", "Can't un-subscribe the group owner from: %s@%s" %(group_name, host))
		else:
			user.delete()
			relay.reply(message, NO_REPLY, "Success", "You are now un-subscribed from: %s@%s" %(group_name, host))
	except User.DoesNotExist:
		relay.reply(message, NO_REPLY, "Error", "You are not subscribed to: %s@%s" %(group_name, host))
        except Group.DoesNotExist:
       	 	relay.reply(message, NO_REPLY, "Error", "Could not locate %s@%s group" %(group_name, host))
        return


@route("(group_name)-info@(host)", group_name=".+", host=HOST)
@stateless
def info(message, group_name=None, host=None):
	group_name = group_name.lower()
        try:
                group = Group.objects.get(name=group_name)
		members = User.objects.filter(group=group).values()
                relay.reply(message, NO_REPLY, "Success", "Group Name: %s@%s, Status: %s, Members: %s" %(group_name, host, group.status, str(members)))
        except Group.DoesNotExist:
		relay.reply(message, NO_REPLY, "Error", "Could not locate %s@%s group" %(group_name, host))
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
	try:
		group = Group.objects.get(name=group_name)
		id = base64.b64encode(addr+str(time.time())).lower()
		p = Post(id = id, from_email = addr, subject = message['Subject'], message=str(message))
		p.save()
		post_addr = '%s <%s>' %(addr, id + SUFFIX + '@' + HOST)
		message['Subject'] = '[ %s ] -- %s' %(group_name, message['Subject'])
		message['From'] = post_addr
		message['To'] = addr
		relay.deliver(message)
	except Group.DoesNotExist:
		relay.reply(message, NO_REPLY, "Error", "Invalid address: %s@%s" %(group_name, host))
	except Exception, e:
		logging.debug('Exception: %s' %(e))
	return


@route("(post_id)(suffix)@(host)", post_id=".+", suffix=SUFFIX+"|"+SUFFIX.upper(), host=HOST)
@stateless
def handle_reply(message, post_id=None, suffix=None, host=None):
	name, addr = parseaddr(message['from'].lower())
	post_id = post_id.lower()
        try:
                post = Post.objects.get(id=post_id)
		r = Reply(from_email = addr, message = post, reply = str(message))
		r.save()
                message['From'] = '%s <%s>' %(addr, post_id + SUFFIX + '@' + HOST)
                message['To'] = addr
                relay.deliver(message)
        except Post.DoesNotExist:
		relay.reply(message, NO_REPLY, "Error", "Invalid post:%s" %(post_id))
        except Exception, e:
                logging.debug('Exception: %s' %(e))
	return




@route("(address)@(host)", address="help", host=HOST)
@stateless
def help(message, address=None, host=None):
	relay.reply(message, address + '@' + HOST, "Help", "For creating a new post, simply send an email to the group email address. For replying to a post, reply to the from_address of the post (just hit the reply button in your email client). For administrative activities like creating, activating, deactivating, subscribing to, unsubscribing from, and viewing a group,  send an email to <group>-[create | activate | deactivate | subscribe | unsubscribe | info]@%s respectively." %(host) )
	return


