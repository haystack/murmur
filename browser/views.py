from django.http import *
from django.shortcuts import render_to_response
import engine.main
from engine.msg_codes import *

from lamson.mail import MailResponse
from config.settings import *
from smtp_handler.utils import *

from django.core.context_processors import csrf
import json

'''
@author: Anant Bhardwaj
@date: Nov 9, 2012

MailX Web Handler
'''

request_error = json.dumps({'code': msg_code['REQUEST_ERROR'],'status':False})
SESSION_KEY = 'USER'

def init_session(email):
	pass

def login_form(request):
	c = {}
	c.update(csrf(request))
	return render_to_response('login.html', c)

def login(request, redirect_url='posts'):
	if request.method == "POST":
		try:
			user = request.POST["email"]
			if(user != ""):
				request.session.flush()
				request.session[SESSION_KEY] = user
				return HttpResponseRedirect(redirect_url)
			else:
				return login_form(request)
		except:
			return login_form(request)
	else:
		return login_form(request)
		


def logout(request):
	request.session.flush()
	return HttpResponseRedirect('posts')


def index(request):
	return HttpResponseRedirect('posts')
		
def posts(request):
	try:
		user = request.session[SESSION_KEY]
		return render_to_response("posts.html", {'user': user})
	except KeyError:
		return HttpResponseRedirect('login')
	
def groups(request):
	try:
		user = request.session[SESSION_KEY]
		return render_to_response("groups.html", {'user': user})
	except KeyError:
		return HttpResponseRedirect('login')
	


def list_groups(request):
	try:
		res = engine.main.list_groups()
		res.update({'user': request.session[SESSION_KEY]})
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")



def create_group(request):
	try:
		res = engine.main.create_group(request.POST['group_name'], request.POST['requester_email'])
		res.update({'user': request.session[SESSION_KEY]})
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")




def activate_group(request):
	try:
		res = engine.main.activate_group(request.POST['group_name'], request.POST['requester_email'])
		res.update({'user': request.session[SESSION_KEY]})
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")




def deactivate_group(request):
	try:
		res = engine.main.deactivate_group(request.POST['group_name'], request.POST['requester_email'])
		res.update({'user': request.session[SESSION_KEY]})
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")




def subscribe_group(request):
	try:
		res = engine.main.subscribe_group(request.POST['group_name'], request.POST['requester_email'])
		res.update({'user': request.session[SESSION_KEY]})
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")
	



def unsubscribe_group(request):
	try:
		res = engine.main.unsubscribe_group(request.POST['group_name'], request.POST['requester_email'])
		res.update({'user': request.session[SESSION_KEY]})
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")



def group_info(request):
	try:
		res = engine.main.group_info(request.POST['group_name'])
		res.update({'user': request.session[SESSION_KEY]})
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")


def list_posts(request):
	try:
		res = engine.main.list_posts()
		res.update({'user': request.session[SESSION_KEY]})
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")


def load_post(request):
	try:
		res = engine.main.load_post(group_name=None, thread_id = request.POST['thread_id'], msg_id=request.POST['msg_id'])
		res.update({'user': request.session[SESSION_KEY]})
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")


def insert_post(request):
	try:
		res = engine.main.insert_post(request.POST['group_name'], request.POST['subject'],  request.POST['msg_text'], request.POST['poster_email'])
		res.update({'user': request.session[SESSION_KEY]})
		msg_id = res['msg_id']
		thread_id = res['thread_id']
		to_send =  res['recipients']
		post_addr = '%s <%s>' %(request.POST['group_name'], request.POST['group_name'] + '+' + str(thread_id) + '+' + str(msg_id) + POST_SUFFIX + '@' + HOST)
		mail = MailResponse(From = request.POST['poster_email'], To = post_addr, Subject  = '[ %s ] -- %s' %(request.POST['group_name'], request.POST['subject']))
		ps_blurb = html_ps(thread_id, msg_id, request.POST['group_name'], HOST)
		mail.Html = request.POST['msg_text'] + ps_blurb		
		logging.debug('TO LIST: ' + str(to_send))
		if(len(to_send)>0):
			relay.deliver(mail, To = to_send)

		return HttpResponse(json.dumps(res), mimetype="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, mimetype="application/json")
		
	


def insert_reply(request):
	try:
		res = engine.main.insert_reply(request.POST['group_name'], request.POST['subject'], request.POST['msg_text'], request.POST['poster_email'], request.POST['msg_id'], request.POST['thread_id'])
		res.update({'user': request.session[SESSION_KEY]})
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")
	


def follow_thread(request):
	try:
		res = engine.main.follow_thread(request.POST['thread_id'], request.POST['requester_email'])
		res.update({'user': request.session[SESSION_KEY]})
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")



def unfollow_thread(request):
	try:
		res = engine.main.unfollow_thread(request.POST['thread_id'], request.POST['requester_email'])
		res.update({'user': request.session[SESSION_KEY]})
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")





