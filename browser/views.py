from django.http import *
from django.contrib.auth.decorators import login_required
from django.utils.encoding import *
import engine.main
from engine.constants import *

from browser.util import load_groups


from lamson.mail import MailResponse
from smtp_handler.utils import *

from django.core.context_processors import csrf
import json, logging
from django.shortcuts import render_to_response, get_object_or_404, redirect

from annoying.decorators import render_to
from schema.models import UserProfile, Group
from html2text import html2text

'''
@author: Anant Bhardwaj
@date: Nov 9, 2012

MailX Web Handler
'''

request_error = json.dumps({'code': msg_code['REQUEST_ERROR'],'status':False})

def logout(request):
	request.session.flush()
	return HttpResponseRedirect('/')

@render_to('404.html')
def error(request):
	user = get_object_or_404(UserProfile, email=request.user.email)
	groups = Group.objects.filter(members__in=[user]).values("name")
	res = {'user': request.user, 'groups': groups, 'group_page': True, 'my_groups': True}
	
	error = request.GET.get('e')
	if error == 'gname':
		res['error'] = '%s is not a valid group name.' % request.GET['group_name']
	elif error == 'admin':
		res['error'] = 'You do not have the admin privileges to visit this page.'
	else:
		res['error'] = 'Unknown error.'
	return res


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
	active_group = load_groups(request, groups, user)
	return {'user': user, "active_group": active_group, "groups": groups}

@render_to("settings.html")
@login_required
def settings(request):
	user = get_object_or_404(UserProfile, email=request.user.email)
	groups = Group.objects.filter(members__in=[user]).values("name")
	active_group = load_groups(request, groups, user)
	return {'user': request.user, "active_group": active_group, "groups": groups}
	
@render_to("groups.html")
@login_required
def my_groups(request):
	user = get_object_or_404(UserProfile, email=request.user.email)
	groups = Group.objects.filter(members__in=[user]).values("name")
	return {'user': request.user, 'groups': groups, 'group_page': True, 'my_groups': True}
	
@render_to("group_page.html")
@login_required
def group_page(request, group_name):
	user = get_object_or_404(UserProfile, email=request.user.email)
	groups = Group.objects.filter(members__in=[user])
	group_info = engine.main.group_info_page(user, group_name)
	if group_info['group']:
		return {'user': request.user, 'groups': groups, 'group_info': group_info, 'group_page': True}
	else:
		return redirect('/404?e=gname&name=%s' % group_name)
	
	
@render_to("list_groups.html")
@login_required
def group_list(request):
	user = get_object_or_404(UserProfile, email=request.user.email)
	groups = Group.objects.filter(members__in=[user]).values("name")
	pub_groups = engine.main.list_groups(user)
	return {'user': request.user, 'groups': groups, 'pub_groups': pub_groups, 'group_page': True}

@render_to("add_members.html")
@login_required
def add_members_view(request, group_name):
	user = get_object_or_404(UserProfile, email=request.user.email)
	groups = Group.objects.filter(members__in=[user])
	try:
		group = Group.objects.get(name=group_name)
		if group.admins.filter(email=user.email).count() > 0:
			return {'user': request.user, 'groups': groups, 'group_info': group, 'group_page': True}
		else:
			return redirect('/404?e=admin')
	except Group.DoesNotExist:
		return redirect('/404?e=gname&name=%s' % group_name)


@login_required
def list_my_groups(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.list_my_groups(user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")


@login_required
def create_group(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		public = request.POST['public'] == 'public'
		res = engine.main.create_group(request.POST['group_name'], request.POST['group_desc'], public, user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")



@login_required
def activate_group(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.activate_group(request.POST['group_name'], user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")



@login_required
def deactivate_group(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.deactivate_group(request.POST['group_name'], user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")


@login_required
def add_members(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.add_members(request.POST['group_name'], request.POST['emails'], user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")
	

@login_required
def subscribe_group(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.subscribe_group(request.POST['group_name'], user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")
	


@login_required
def unsubscribe_group(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.unsubscribe_group(request.POST['group_name'], user)
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
		group_name = request.POST.get('active_group')
		res = engine.main.list_posts(group_name=group_name)
		res['user'] = request.user.email
		return HttpResponse(json.dumps(res), content_type="application/json")
	except  Exception, e:
		logging.debug(e)
		print e
		return HttpResponse(request_error, content_type="application/json")

@login_required
def refresh_posts(request):
	try:
		group_name = request.POST.get('active_group')
		res = engine.main.list_posts(group_name=group_name, timestamp_str = request.POST['timestamp'])
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
		user = get_object_or_404(UserProfile, email=request.user.email)

		group_name = request.POST['group_name'].encode('ascii', 'ignore')
		subject = '[ %s ] %s' %(group_name, request.POST['subject'].encode('ascii', 'ignore'))
		
		msg_text = request.POST['msg_text'].encode('ascii', 'ignore')

		res = engine.main.insert_post(group_name, subject,  msg_text, user)
		
		
		msg_id = res['msg_id']
		to_send =  res['recipients']
		
		post_addr = '%s <%s>' %(group_name, group_name + '@' + HOST)
		mail = MailResponse(From = user.email, To = post_addr, Subject  = subject)
		
		
		mail.update({
				"Sender": post_addr, 
				"Reply-To": post_addr,
				"List-Id": post_addr,
				"List-Unsubscribe": "<mailto:%s+unsubscribe@%s>" % (group_name, HOST),
				"List-Archive": "<http://%s/groups/%s/>" % (HOST, group_name),
				"List-Post": "<mailto:%s>" % post_addr,
				"List-Help": "<mailto:help@%s>" % HOST,
				"List-Subscribe": "<mailto:%s+subscribe@%s>" % (group_name,HOST),
				"Return-Path": post_addr, 
				"Precedence": 'list',
			})
		
		mail['message-id'] = msg_id
		
		ps_blurb = html_ps(group_name, HOST)
		mail.Html = msg_text + ps_blurb	
		
		ps_blurb = plain_ps(group_name, HOST)
		mail.Body = html2text(msg_text) + ps_blurb	
		
		
		logging.debug('TO LIST: ' + str(to_send))
		if(len(to_send)>0):
			relay_mailer.deliver(mail, To = to_send)

		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")
		
	

@login_required
def insert_reply(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		group_name = request.POST['group_name'].encode('ascii', 'ignore')
		subject = request.POST['subject'].encode('ascii', 'ignore')
		msg_text = request.POST['msg_text'].encode('ascii', 'ignore')
		msg_id = request.POST['msg_id'].encode('ascii', 'ignore')
		thread_id = request.POST.get('thread_id', None)
		
		res = engine.main.insert_reply(group_name, subject, msg_text, user, thread_id=thread_id)
		if(res['status']):
			
			to_send =  res['recipients']
			post_addr = '%s <%s>' %(group_name, group_name + '@' + HOST)
			mail = MailResponse(From = user.email, To = post_addr, Subject  = '%s' %(subject))
			
			mail['References'] = msg_id		
			mail['message-id'] = res['msg_id']
			
			mail["In-Reply-To"] = msg_id
				
			mail.update({
				"Sender": post_addr, 
				"Reply-To": post_addr,
				"List-Id": post_addr,
				"List-Unsubscribe": "<mailto:%s+unsubscribe@%s>" % (group_name, HOST),
				"List-Archive": "<http://%s/groups/%s/>" % (HOST, group_name),
				"List-Post": "<mailto:%s>" % post_addr,
				"List-Help": "<mailto:help@%s>" % HOST,
				"List-Subscribe": "<mailto:%s+subscribe@%s>" % (group_name,HOST),
				"Return-Path": post_addr, 
				"Precedence": 'list',
			})
				
			ps_blurb = html_ps(group_name, HOST)
			mail.Html = msg_text + ps_blurb		
			
			ps_blurb = plain_ps(group_name, HOST)
			mail.Body = html2text(msg_text) + ps_blurb	
			
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
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.follow_thread(request.POST['thread_id'], user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")


@login_required
def unfollow_thread(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.unfollow_thread(request.POST['thread_id'], user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")





