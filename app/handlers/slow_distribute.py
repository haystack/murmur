import logging
from lamson.routing import route, route_like, stateless
from config.settings import relay



@route("(address)@(host)", address=".+", host=".+")
@stateless
def START(message, address=None, host=None):
	logging.debug("%s" %(str(message)))
	relay.reply(message, 'no-reply@slow.csail.mit.edu', 'Auto: ' + message['Subject'], message.body())
	return
