import logging
from lamson.routing import route, stateless
import logging
import email


def get_first_text_block(email_message_instance):
	maintype = email_message_instance.get_content_maintype()
	if maintype == 'multipart':
		for part in email_message_instance.get_payload():
			if part.get_content_maintype() == 'text':
				return part.get_payload()
	elif maintype == 'text':
		return email_message_instance.get_payload()


@route("(address)@(host)", address=".+", host="slow.csail.mit.edu")
@stateless
def START(message, address=None, host=None):
    email_message = email.message_from_string(str(message))
    body = get_first_text_block(email_message)   
    logging.debug("%s %s %s" %(body, address, host))
    return


