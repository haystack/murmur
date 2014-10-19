from django.http import *
from django.contrib.auth.decorators import login_required
from django.utils.encoding import *
import engine.main
from engine.msg_codes import *


from lamson.mail import MailResponse
from smtp_handler.utils import *

from django.core.context_processors import csrf
import json, logging
from django.shortcuts import render_to_response, get_object_or_404

from annoying.decorators import render_to
from schema.models import UserProfile, Group

'''
@author: Anant Bhardwaj
@date: Nov 9, 2012

MailX Web Handler
'''

request_error = json.dumps({'code': msg_code['REQUEST_ERROR'],'status':False})

def logout(request):
	request.session.flush()
	return HttpResponseRedirect('/')

@render_to('home.html')
def index(request):
	if not request.user.is_authenticated():
		return dict()
	else:
		return HttpResponseRedirect('/posts')

@render_to("posts.html")
@login_required
def posts(request):
	user = get_object_or_404(UserProfile, email=request.user.email)
	
	groups = Group.objects.filter(members__in=[user]).values("name")
	
	active_group = request.GET.get('group_name')
	if active_group:
		request.session['active_group'] = active_group
		active_group = {'name': active_group}
	elif request.session.get('active_group'):
		active_group = request.session.get('active_group')
		active_group = {'name': active_group}
	else:
		active_group = groups[0]
		
	return {'user': user, "active_group": active_group, "groups": groups}

@render_to("settings.html")
@login_required
def settings(request):
	return {'user': request.user}
	
@render_to("groups.html")
@login_required
def groups(request):
	return {'user': request.user, 'group_page': True}
	
@login_required
def list_groups(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.list_groups(user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")


@login_required
def create_group(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		
		# for now, all groups are public
		public = True
		res = engine.main.create_group(request.POST['group_name'], public, user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")



@login_required
def activate_group(request):
	try:
		res = engine.main.activate_group(request.POST['group_name'], request.user.email)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")



@login_required
def deactivate_group(request):
	try:
		res = engine.main.deactivate_group(request.POST['group_name'], request.user.email)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")



@login_required
def subscribe_group(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		
		res = engine.main.subscribe_group(request.POST['group_name'], user.email)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")
	


@login_required
def unsubscribe_group(request):
	try:
		res = engine.main.unsubscribe_group(request.POST['group_name'], request.user.email)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")


@login_required
def group_info(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.group_info(request.POST['group_name'], user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def list_posts(request):
	try:
		res = engine.main.list_posts()
		return HttpResponse(json.dumps(res), content_type="application/json")
	except  Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def refresh_posts(request):
	try:
		res = engine.main.list_posts(timestamp_str = request.POST['timestamp'])
		return HttpResponse(json.dumps(res), content_type="application/json")
	except  Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")


@login_required
def load_post(request):
	try:
		res = engine.main.load_post(group_name=None, thread_id = request.POST['thread_id'], msg_id=request.POST['msg_id'])
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def insert_post(request):
	try:
		group_name = request.POST['group_name'].encode('ascii', 'ignore')
		subject = '[ %s ] -- %s' %(group_name, request.POST['subject'].encode('ascii', 'ignore'))
		msg_text = request.POST['msg_text'].encode('ascii', 'ignore')
		poster_email = request.user.email.encode('ascii', 'ignore')
		res = engine.main.insert_post(group_name, subject,  msg_text, poster_email)
		msg_id = res['msg_id']
		thread_id = res['thread_id']
		to_send =  res['recipients']
		
		post_addr = '%s <%s>' %(group_name, group_name + '+' + str(thread_id) + '+' + str(msg_id) + POST_SUFFIX + '@' + HOST)
		mail = MailResponse(From = poster_email, To = post_addr, Subject  = subject)
		mail['message-id'] = msg_id
		
		ps_blurb = html_ps(thread_id, msg_id, group_name, HOST)
		mail.Html = msg_text + ps_blurb	
		logging.debug('TO LIST: ' + str(to_send))
		if(len(to_send)>0):
			relay_mailer.deliver(mail, To = to_send)

		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")
		
	

@login_required
def insert_reply(request):
	try:
		group_name = request.POST['group_name'].encode('ascii', 'ignore')
		subject = request.POST['subject'].encode('ascii', 'ignore')
		msg_text = request.POST['msg_text'].encode('ascii', 'ignore')
		msg_id = request.POST['msg_id'].encode('ascii', 'ignore')
		thread_id = request.POST['thread_id'].encode('ascii', 'ignore')
		poster_email = request.user.email.encode('ascii', 'ignore')
		res = engine.main.insert_reply(group_name, subject, msg_text, poster_email, msg_id, thread_id)
		if(res['status']):
			new_msg_id = res['msg_id']
			thread_id = res['thread_id']
			to_send =  res['recipients']
			post_addr = '%s <%s>' %(group_name, group_name + '+' + str(thread_id) + '+' + str(new_msg_id) + POST_SUFFIX + '@' + HOST)
			mail = MailResponse(From = poster_email, To = post_addr, Subject  = '%s' %(subject))
			
			
			mail['References'] = msg_id		
			mail['message-id'] = new_msg_id
				
			ps_blurb = html_ps(thread_id, msg_id, group_name, HOST)
			mail.Html = msg_text + ps_blurb		
			logging.debug('TO LIST: ' + str(to_send))
			if(len(to_send)>0):
				relay_mailer.deliver(mail, To = to_send)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print sys.exc_info()
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")
	

@login_required
def follow_thread(request):
	try:
		res = engine.main.follow_thread(request.POST['thread_id'], request.user.email)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")


@login_required
def unfollow_thread(request):
	try:
		res = engine.main.unfollow_thread(request.POST['thread_id'], request.user.email)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")





