import logging
from lamson.routing import route, route_like, stateless
from config.settings import relay
from models import *

'''
Slow_Email Main Handler

@author: Anant Bhardwaj
@date: Oct 20, 2012
'''

@route("(address)@(host)", address=".+", host="slow.csail.mit.edu")
@stateless
def START(message, address=None, host=None):
	p = Post(from_addr = message['From'], message=str(message))
	p.save()
	relay.reply(message, 'no-reply@slow.csail.mit.edu', message['Subject'], message.body())
	return
