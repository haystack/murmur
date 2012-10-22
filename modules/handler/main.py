import logging
from lamson.routing import route, route_like, stateless
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

@route("(address)-add@(host)", address=".+", host=HOST)
@stateless
def add(message, address=None, host=None):
        relay.reply(message, NO_REPLY, "Success", "List Added: %s@slow.csail.mit.edu" %(address))
        return

@route("(address)-subscribe@(host)", address=".+", host=HOST)
@stateless
def subscribe(message, address=None, host=None):
        relay.reply(message, NO_REPLY, "Success", "Subscribed to: %s@slow.csail.mit.edu" %(address))
        return

@route("(address)-unsubscribe@(host)", address=".+", host=HOST)
@stateless
def unsubscribe(message, address=None, host=None):
        relay.reply(message, NO_REPLY, "Success", "Unsubscribed from: %s@slow.csail.mit.edu" %(address))
        return


@route("(address)-info@(host)", address=".+", host=HOST)
@stateless
def info(message, address=None, host=None):
        relay.reply(message, NO_REPLY, "Success", "List Info: %s@slow.csail.mit.edu" %(address))
        return


@route("(address)@(host)", address="ask", host=HOST)
@stateless
def handle(message, address=None, host=None):
	name, addr = parseaddr(message['from'])
	p = Post(from_addr = addr, message=str(message))
	p.save()
	relay.reply(message, address + '@' + HOST, message['Subject'], message.body())
	return


