from django.http import *
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
import engine.main
from engine.msg_codes import *
from django.views.decorators.csrf import csrf_exempt
import json

'''
@author: Anant Bhardwaj
@date: Nov 9, 2012

MailX Web Handler
'''

request_error = json.dumps({'code': msg_code['REQUEST_ERROR'],'status':False})


def index(request):
	return render_to_response("index.html")

@csrf_exempt
def list_groups(request):
	try:
		res = engine.main.list_groups()
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")


@csrf_exempt
def create_group(request):
	try:
		res = engine.main.create_group(request.POST['group_name'], request.POST['requester_email'])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")



@csrf_exempt
def activate_group(request):
	try:
		res = engine.main.activate_group(request.POST['group_name'], request.POST['requester_email'])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")



@csrf_exempt
def deactivate_group(request):
	try:
		res = engine.main.deactivate_group(request.POST['group_name'], request.POST['requester_email'])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")



@csrf_exempt
def subscribe_group(request):
	try:
		res = engine.main.subscribe_group(request.POST['group_name'], request.POST['requester_email'])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")
	


@csrf_exempt
def unsubscribe_group(request):
	try:
		res = engine.main.unsubscribe_group(request.POST['group_name'], request.POST['requester_email'])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")


@csrf_exempt
def group_info(request):
	try:
		res = engine.main.group_info(request.POST['group_name'], request.POST['requester_email'])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")



@csrf_exempt
def insert_post(request):
	try:
		res = engine.main.insert_post(request.POST['group_name'], request.POST['message'], request.POST['poster_email'])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")
	

@csrf_exempt
def insert_reply(request):
	try:
		res = engine.main.insert_reply(request.POST['group_name'], request.POST['message'], request.POST['poster_email'], request.POST['post_id'])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")
	

@csrf_exempt
def follow_post(request):
	try:
		res = engine.main.follow_post(request.POST['group_name'], request.POST['requester_email'])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")


@csrf_exempt
def unfollow_post(request):
	try:
		res = engine.main.unfollow_post(request.POST['group_name'], request.POST['requester_email'])
		return HttpResponse(json.dumps(res), mimetype="application/json")
	except:
		return HttpResponse(request_error, mimetype="application/json")



	