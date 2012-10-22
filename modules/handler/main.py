import logging
from lamson.routing import route, route_like, stateless
from config.settings import relay
from models import *

'''
Slow_Email Main Handler

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''

@route("(address)@(host)", address="ask", host="slow.csail.mit.edu")
@stateless
def START(message, address=None, host=None):
	p = Post(from_addr = message['From'], message=str(message))
	p.save()
	relay.reply(message, 'ask@slow.csail.mit.edu', message['Subject'], message.body())
	return


@route("(address)@(host)", address="some", host="slow.csail.mit.edu")
@stateless
def START(message, address=None, host=None):
	p = Post(from_addr = message['From'], message=str(message))
	p.save()
	relay.reply(message, 'some@slow.csail.mit.edu', message['Subject'], message.body())
	return


@route("(address)-subscribe@(host)", address=".+", host="slow.csail.mit.edu")
@stateless
def START(message, address=None, host=None):
        relay.reply(message, 'no-reply@slow.csail.mit.edu', "Success", "List Address: %s@slow.csail.mit.edu" %(address))
        return
