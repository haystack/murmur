from django.http import *
from django.shortcuts import render_to_response
import engine.main
from engine.msg_codes import *
from django.views.decorators.csrf import csrf_exempt
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

def login(request, redirect_url='index'):
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
	return HttpResponseRedirect('index')


def index(request):
	try:
		user = request.session[SESSION_KEY]
		return render_to_response("index.html", {'user': user})
	except KeyError:
		return login_form(request)
		
	
def settings(request):
	try:
		user = request.session[SESSION_KEY]
		return render_to_response("settings.html", {'user': user})
	except KeyError:
		return login_form(request)
	

@csrf_exempt
def list_groups(request):
	try:
		res = engine.main.list_groups()
		res.update('user': request.session[SESSION_KEY])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")


@csrf_exempt
def create_group(request):
	try:
		res = engine.main.create_group(request.POST['group_name'], request.POST['requester_email'])
		res.update('user': request.session[SESSION_KEY])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")



@csrf_exempt
def activate_group(request):
	try:
		res = engine.main.activate_group(request.POST['group_name'], request.POST['requester_email'])
		res.update('user': request.session[SESSION_KEY])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")



@csrf_exempt
def deactivate_group(request):
	try:
		res = engine.main.deactivate_group(request.POST['group_name'], request.POST['requester_email'])
		res.update('user': request.session[SESSION_KEY])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")



@csrf_exempt
def subscribe_group(request):
	try:
		res = engine.main.subscribe_group(request.POST['group_name'], request.POST['requester_email'])
		res.update('user': request.session[SESSION_KEY])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")
	


@csrf_exempt
def unsubscribe_group(request):
	try:
		res = engine.main.unsubscribe_group(request.POST['group_name'], request.POST['requester_email'])
		res.update('user': request.session[SESSION_KEY])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")


@csrf_exempt
def group_info(request):
	try:
		res = engine.main.group_info(request.POST['group_name'])
		res.update('user': request.session[SESSION_KEY])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")



@csrf_exempt
def insert_post(request):
	try:
		res = engine.main.insert_post(request.POST['group_name'], request.POST['message'], request.POST['poster_email'])
		res.update('user': request.session[SESSION_KEY])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")
	

@csrf_exempt
def insert_reply(request):
	try:
		res = engine.main.insert_reply(request.POST['group_name'], request.POST['message'], request.POST['poster_email'], request.POST['post_id'])
		res.update('user': request.session[SESSION_KEY])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")
	

@csrf_exempt
def follow_post(request):
	try:
		res = engine.main.follow_post(request.POST['group_name'], request.POST['requester_email'])
		res.update('user': request.session[SESSION_KEY])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")


@csrf_exempt
def unfollow_post(request):
	try:
		res = engine.main.unfollow_post(request.POST['group_name'], request.POST['requester_email'])
		res.update('user': request.session[SESSION_KEY])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")



	