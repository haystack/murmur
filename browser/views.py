from django.http import *
from django.contrib.auth.decorators import login_required
from django.utils.encoding import *
import engine.main
import base64
from engine.constants import *

from browser.util import load_groups

from browser.util import paginator

from lamson.mail import MailResponse
from smtp_handler.utils import *
from http_handler.settings import WEBSITE, AWS_STORAGE_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

from django.core.context_processors import csrf
import json, logging
from django.shortcuts import render_to_response, get_object_or_404, redirect

from annoying.decorators import render_to
from schema.models import UserProfile, Group, MemberGroup, Tag, FollowTag,\
	MuteTag, ForwardingList, Attachment, Post
from html2text import html2text
from django.contrib.auth.forms import AuthenticationForm
from registration.forms import RegistrationForm
from django.conf import global_settings
from django.db.models.aggregates import Count
from django.http import HttpResponse
from django.template.context import RequestContext

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from boto.s3.connection import S3Connection

request_error = json.dumps({'code': msg_code['REQUEST_ERROR'],'status':False})

def lamson_status(request):
	import psutil
	response_text = ""
	if "lamson" in [psutil.Process(i).name() for i in psutil.pids()]:
		response_text = "lamson running"
	response = HttpResponse(response_text)
	return response
	

def logout(request):
	request.session.flush()
	return HttpResponseRedirect('/')

@render_to(WEBSITE+'/about.html')
def about(request):
	return {}

@render_to(WEBSITE+'/404.html')
def error(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")
	else:
		user = None
		groups = []
	res = {'user': request.user, 'groups': groups, 'group_page': True, 'my_groups': True}
	
	error = request.GET.get('e')
	if error == 'gname':
		res['error'] = '%s is not a valid group name.' % request.GET['name']
	elif error == 'admin':
		res['error'] = 'You do not have the admin privileges to visit this page.'
	elif error == 'member':
		res['error'] = 'You need to be a member of this group to visit this page.'
	elif error == 'thread':
		res['error'] = 'This thread no longer exists.'
	else:
		res['error'] = 'Unknown error.'
	return res


@render_to(WEBSITE+'/home.html')
def index(request):
	if not request.user.is_authenticated():
		if WEBSITE == 'murmur':
			return render_to_response('murmur/home.html',
									  {'form': AuthenticationForm(),
									   'reg_form': RegistrationForm()},
									   context_instance=RequestContext(request))
		elif WEBSITE == 'squadbox':
			return render_to_response('squadbox/home.html',
										{'form': AuthenticationForm(),
										'reg_form': RegistrationForm()},
										context_instance=RequestContext(request))
	else:
		return HttpResponseRedirect('/posts')
	
@render_to(WEBSITE+'/posts.html')
def posts(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")
		
		thread_id = request.GET.get('tid')
		if thread_id:
			try:
				group_name = Thread.objects.get(id=thread_id).group.name
			except Thread.DoesNotExist:
				pass
			active_group = load_groups(request, groups, user, group_name=group_name)
		else:
			active_group = load_groups(request, groups, user)
			
		tag_info = None
		member_info = None
		is_member = False

		if active_group['active']:
			group = Group.objects.get(name=active_group['name'])
			active_group['description'] = group.description
			member = MemberGroup.objects.filter(member=user, group=group)
			if member.count() > 0:
				is_member = True
				member_info = member[0]
	
			tag_info = Tag.objects.filter(group=group).annotate(num_p=Count('tagthread')).order_by('-num_p')
			for tag in tag_info:
				tag.muted = tag.mutetag_set.filter(user=user, group=group).exists()
				tag.followed = tag.followtag_set.filter(user=user, group=group).exists()
			
		page_info = {"user": user, 
					"active_group": active_group, 
					"groups": groups, 
					"tag_info": tag_info, 
					"member_info": member_info,
					}
		
		# not a member of any groups
		if not active_group['active']:
			return HttpResponseRedirect('/group_list')
		elif group.public or is_member:
			if request.flavour == "mobile":
				return HttpResponseRedirect('/post_list?group_name=%s' % (active_group['name']))
			else:
				if is_member:
					request.session['active_group'] = active_group['name']
					return page_info
				else:
					return HttpResponseRedirect('/post_list?group_name=%s' % (active_group['name']))
		else:
			if len(groups) == 0:
				return HttpResponseRedirect('/group_list')
			else:
				return redirect('/404?e=member')
		
	else:
		user = None
		groups = []
		active_group = request.GET.get('group_name')
		if active_group:
			group = Group.objects.get(name=active_group)
			if group.public:
				return HttpResponseRedirect('/post_list?group_name=%s' % (active_group))
			else:
				return redirect('/404?e=member')
		else:
			return HttpResponseRedirect(global_settings.LOGIN_URL)
		
		

@render_to(WEBSITE+'/mobile_list_posts.html')
def post_list(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")
		
		active_group = load_groups(request, groups, user)
		is_member = False
		group_name = request.GET.get('group_name')
		if active_group['active']:
			group = Group.objects.get(name=active_group['name'])
			is_member = MemberGroup.objects.filter(member=user, group=group).exists()
			group_name = active_group['name']
			
		if group.public or is_member:
			if is_member:
				request.session['active_group'] = group_name
			res = engine.main.list_posts(group_name=group_name, user=user, format_datetime=False, return_replies=True)
			res['threads'] = paginator(request.GET.get('page'), res['threads'])
			return {'user': request.user, 'groups': groups, 'posts': res, 'active_group': active_group}
		else:
			return redirect('/404?e=member')
	else:
		user = None
		groups = []
		active_group = {'name': request.GET.get('group_name')}
		if active_group['name']:
			group = Group.objects.get(name=active_group['name'])
			if not group.public:
				return redirect('/404?e=member')
			else:
				res = engine.main.list_posts(group_name=request.GET.get('group_name'), format_datetime=False, return_replies=False)
				return {'user': request.user, 'groups': groups, 'posts': res, 'active_group': active_group}
		else:
			return HttpResponseRedirect(global_settings.LOGIN_URL)
		
	

@render_to(WEBSITE+"/thread.html")
def thread(request):
	
	post_id = request.GET.get('post_id')
	thread_id = request.GET.get('tid')
	try:
		thread = Thread.objects.get(id=int(thread_id))
	except Thread.DoesNotExist:
		return redirect('/404?e=thread')
	
	group = thread.group
	
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")
		
		member_group = MemberGroup.objects.filter(member=user, group=group)
		is_member = member_group.exists()
		
		active_group = load_groups(request, groups, user, group_name=group.name)
		if group.public or is_member:
			if is_member:
				res = engine.main.load_thread(thread, user=request.user, member=member_group[0])
			else:
				res = engine.main.load_thread(thread, user=request.user)
			return {'user': request.user, 'groups': groups, 'thread': res, 'post_id': post_id, 'active_group': active_group}
		else:
			if active_group['active']:
				request.session['active_group'] = None
			return redirect('/404?e=member')
	else:
		user = None
		groups = []
		active_group = {'name': group.name}
		if not group.public:
			return HttpResponseRedirect(global_settings.LOGIN_URL)
		else:
			res = engine.main.load_thread(thread)
			return {'user': request.user, 'groups': groups, 'thread': res, 'post_id': post_id,'active_group': active_group}
			
			



@render_to(WEBSITE+"/settings.html")
@login_required
def settings(request):
	user = get_object_or_404(UserProfile, email=request.user.email)
	groups = Group.objects.filter(membergroup__member=user).values("name")
	active_group = load_groups(request, groups, user)
	return {'user': request.user, "active_group": active_group, "groups": groups}
	
@render_to(WEBSITE+"/groups.html")
@login_required
def my_groups(request):
	user = get_object_or_404(UserProfile, email=request.user.email)
	if request.flavour == "mobile":
		return HttpResponseRedirect('/my_group_list')
	else:
		groups = Group.objects.filter(membergroup__member=user).values("name")
		info = engine.main.check_admin(user,groups)
		return {'user': request.user, 'groups': groups, 'group_page': True, 'my_groups': True, 'info':info}



@render_to(WEBSITE+"/mobile_list_groups.html")
@login_required
def my_group_list(request):
	user = get_object_or_404(UserProfile, email=request.user.email)
	groups = engine.main.list_my_groups(user)
	return {'user': request.user, 'groups': groups['groups'], 'group_page': True, 'my_groups': True}


@render_to(WEBSITE+"/mobile_pub_list_groups.html")
def pub_group_list(request):
	groups = engine.main.list_groups()
	return {'user': request.user, 'pub_groups': groups, 'group_page': True}

	
@render_to(WEBSITE+"/group_page.html")
def group_page(request, group_name):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")
	except Exception:
		user = None
		groups = []
		
	group_info = engine.main.group_info_page(user, group_name)
	if group_info['group']:
		return {'user': request.user, 'groups': groups, 'group_info': group_info, 'group_page': True, 'admin_address' : group_name + '+admins@' + HOST}
	else:
		return redirect('/404?e=gname&name=%s' % group_name)
	
	
@render_to(WEBSITE+"/list_groups.html")
def group_list(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")
	except Exception:
		user = None
		groups = []
	pub_groups = engine.main.list_groups(user)
	if request.flavour == "mobile":
		return HttpResponseRedirect('/pub_group_list')
	else:
		return {'user': request.user, 'groups': groups, 'pub_groups': pub_groups, 'group_page': True}

@render_to(WEBSITE+"/add_members.html")
@login_required
def add_members_view(request, group_name):
	user = get_object_or_404(UserProfile, email=request.user.email)
	groups = Group.objects.filter(membergroup__member=user).values("name")
	try:
		group = Group.objects.get(name=group_name)
		membergroup = MemberGroup.objects.filter(member=user, group=group)
		if membergroup.count() == 1 and membergroup[0].admin:
			return {'user': request.user, 'groups': groups, 'group_info': group, 'group_page': True}
		else:
			return redirect('/404?e=admin')
	except Group.DoesNotExist:
		return redirect('/404?e=gname&name=%s' % group_name)

@render_to(WEBSITE+"/add_list.html")
@login_required
def add_list_view(request, group_name):
	user = get_object_or_404(UserProfile, email=request.user.email)
	groups = Group.objects.filter(membergroup__member=user).values("name")
	try:
		group = Group.objects.get(name=group_name)
		membergroup = MemberGroup.objects.filter(member=user, group=group)
		if membergroup.count() == 1 and membergroup[0].admin:
			return {'user': request.user, 'groups': groups, 'group_info': group, 'group_page': True}
		else:
			return redirect('/404?e=admin')
	except Group.DoesNotExist:
		return redirect('/404?e=gname&name=%s' % group_name)

@render_to(WEBSITE+"/edit_my_settings.html")
@login_required
def my_group_settings_view(request, group_name):
	user = get_object_or_404(UserProfile, email=request.user.email)
	groups = Group.objects.filter(membergroup__member=user).values("name")
	try:
		group = Group.objects.get(name=group_name)
		membergroup = MemberGroup.objects.get(member=user, group=group)
		return {'user': request.user, 'groups': groups, 'group_info': group, 'settings': membergroup, 'group_page': True}
	except Group.DoesNotExist:
		return redirect('/404?e=gname&name=%s' % group_name)
	except MemberGroup.DoesNotExist:
		return redirect('/404?e=member')
	
@render_to(WEBSITE+"/create_post.html")
@login_required
def my_group_create_post_view(request, group_name):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")
		try:
			group = Group.objects.get(name=group_name)
			member = MemberGroup.objects.get(member=user, group=group)
			return {'user': request.user, 'groups': groups, 'group_info': group, 'group_page': True}
		except Group.DoesNotExist:
			return redirect('/404?e=gname&name=%s' % group_name)
		except MemberGroup.DoesNotExist:
			return redirect('/404?e=member')
	else:
		return HttpResponseRedirect(global_settings.LOGIN_URL)

@login_required
def list_my_groups(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.list_my_groups(user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@render_to(WEBSITE+"/create_group.html")
@login_required
def create_group_view(request):
	user = get_object_or_404(UserProfile, email=request.user.email)
	groups = Group.objects.filter(membergroup__member=user).values("name")
	return {'user': request.user, 'groups': groups, 'group_page': True}


@render_to(WEBSITE+"/edit_group_info.html")
@login_required
def edit_group_info_view(request, group_name):
	user = get_object_or_404(UserProfile, email=request.user.email)  
	groups = Group.objects.filter(membergroup__member=user).values("name")  #defines the user and the groups this user is in.
	try:
		group = Group.objects.get(name=group_name)
		membergroup = MemberGroup.objects.filter(member=user, group=group)
		if membergroup[0].admin:
			return {'user': request.user, 'groups': groups, 'group_info': group, 'group_page': True}
		else:
			return redirect('/404?e=admin')
	except Group.DoesNotExist:
		return redirect('/404?e=gname&name=%s' % group_name)


@login_required
def edit_group_info(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		old_group_name = request.POST['old_group_name']  
		new_group_name = request.POST['new_group_name']
		group_desc = request.POST['group_desc'] 
		public = request.POST['public'] == 'public'
		attach = request.POST['attach'] == 'yes-attach'
		res = engine.main.edit_group_info(old_group_name, new_group_name, group_desc, public, attach, user) 
		if res['status']:
			active_group = request.session.get('active_group')
			if active_group == old_group_name:
				request.session['active_group'] = new_group_name

		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def edit_members(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.edit_members_table(request.POST['group_name'], request.POST['toDelete'], request.POST['toAdmin'], request.POST['toMod'], user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def delete_group(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.delete_group(request.POST['group_name'], user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def create_group(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		public = request.POST['public'] == 'public'
		attach = request.POST['attach'] == 'yes-attach'
		res = engine.main.create_group(request.POST['group_name'], request.POST['group_desc'], public, attach, user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")


def get_group_settings(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.get_group_settings(request.POST['group_name'], user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")


@login_required
def edit_group_settings(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		following = request.POST['following'] == 'yes'
		upvote_emails = request.POST['upvote_emails'] == 'true'
		no_emails = request.POST['no_emails'] == 'true'
		res = engine.main.edit_group_settings(request.POST['group_name'], following, upvote_emails, no_emails, user)
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
def add_list(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		can_receive = False
		can_post = False
		if request.POST['can_receive'] == 'true':
			can_receive = True
		if request.POST['can_post'] == 'true':
			can_post = True
		res = engine.main.add_list(request.POST['group_name'], request.POST['email'], 
			can_receive, can_post, request.POST['list_url'], user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def delete_list(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.delete_list(request.POST['group_name'], request.POST['lists'], user)
		return HttpResponse(json.dumps(res), content_type='application/json')
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def adjust_list_can_post(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		can_post = False 
		if request.POST['can_post'] == 'true':
			can_post = True
		res = engine.main.adjust_list_can_post(request.POST['group_name'], request.POST['lists'], can_post, user)
		return HttpResponse(json.dumps(res), content_type='application/json')
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def adjust_list_can_receive(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		can_receive = False 
		if request.POST['can_receive'] == 'true':
			can_receive = True
		res = engine.main.adjust_list_can_receive(request.POST['group_name'], request.POST['lists'], can_receive, user)
		return HttpResponse(json.dumps(res), content_type='application/json')
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

def subscribe_group(request):
	try:
		if request.user.is_authenticated():
		
			user = get_object_or_404(UserProfile, email=request.user.email)
			res = engine.main.subscribe_group(request.POST['group_name'], user)
			return HttpResponse(json.dumps(res), content_type="application/json")
		
		else:
			group = request.POST['group_name']
			return HttpResponse(json.dumps({'redirect': True, 
										'url': global_settings.LOGIN_URL + "?next=/groups/" + group}), 
										content_type="application/json")
	

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
		res['admin_email'] = request.POST['group_name'] + '+admins@' + HOST
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def list_posts(request):
	print "LIST POST"
	try:
		group_name = request.POST.get('active_group')
		res = engine.main.list_posts(group_name=group_name, user=request.user.email)
		res['user'] = request.user.email
		res['group_name'] = group_name
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		print e
		return HttpResponse(request_error, content_type="application/json")

@login_required
def refresh_posts(request):
	try:
		group_name = request.POST.get('active_group')
		if request.user.is_authenticated():
			user = get_object_or_404(UserProfile, email=request.user.email)
		else:
			user = None
		res = engine.main.list_posts(group_name=group_name, user=user, timestamp_str = request.POST['timestamp'])
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

		group_name = request.POST['group_name']
		
		msg_text = request.POST['msg_text']
		
		res = engine.main.insert_post_web(group_name, request.POST['subject'], msg_text, user)
		
		subj_tag = ''
		for tag in res['tags']:
			subj_tag += '[%s]' % tag['name']
			
		stripped_subj = re.sub("\[.*?\]", "", request.POST['subject'])
		subject = '[%s]%s %s' %(group_name, subj_tag, stripped_subj)
		
		
		msg_id = res['msg_id']
		to_send =  res['recipients']
		
		post_addr = '%s <%s>' %(group_name, group_name + '@' + HOST)
		
		mail = setup_post(user.email,
					subject,	
					group_name)
		
		mail['message-id'] = msg_id
		
		g = Group.objects.get(name=group_name)
		t = Thread.objects.get(id=res['thread_id'])
		
		if len(to_send) > 0:
			
			recips = UserProfile.objects.filter(email__in=to_send)
			membergroups = MemberGroup.objects.filter(group=g, member__in=recips)
			
			followings = Following.objects.filter(thread=t, user__in=recips)
			mutings = Mute.objects.filter(thread=t, user__in=recips)
			
			tag_followings = FollowTag.objects.filter(group=g, tag__in=res['tag_objs'], user__in=recips)
			tag_mutings = MuteTag.objects.filter(group=g, tag__in=res['tag_objs'], user__in=recips)
			
			
			for recip in recips:
				membergroup = membergroups.filter(member=recip)[0]
				following = followings.filter(user=recip).exists()
				muting = mutings.filter(user=recip).exists()
				tag_following = tag_followings.filter(user=recip)
				tag_muting = tag_mutings.filter(user=recip)

				original_group = None
				if request.POST.__contains__('original_group'):
					original_group = request.POST['original_group'] + '@' + HOST

				ps_blurb = html_ps(g, t, res['post_id'], membergroup, following, muting, tag_following, tag_muting, res['tag_objs'], original_group)
				mail.Html = msg_text + ps_blurb	
				
				ps_blurb = plain_ps(g, t, res['post_id'], membergroup, following, muting, tag_following, tag_muting, res['tag_objs'], original_group)
				mail.Body = html2text(msg_text) + ps_blurb	
			
				relay_mailer.deliver(mail, To = recip.email)

		fwding_lists = ForwardingList.objects.filter(group=g, can_receive=True)

		for l in fwding_lists:

			footer_html = html_forwarded_blurb(g.name, l.email)
			mail.Html = msg_text + footer_html
			footer_plain = plain_forwarded_blurb(g.name, l.email)
			mail.Body = html2text(msg_text) + footer_plain

			# non murmur list, send on as usual
			if HOST not in l.email:
				relay_mailer.deliver(mail, To = l.email)

			# need to bypass sending email to prevent "loops back to myself" error,
			# so modify request object then recursively call insert_post on it
			else: 
				group_name = l.email.split('@')[0]
				# request.POST is immutable; have to copy, edit, and then reassign
				new_post = request.POST.copy()
				new_post['group_name'] = group_name
				if not new_post.__contains__('original_group'):
					new_post['original_group'] = request.POST['group_name']
				request.POST = new_post
				insert_post(request)

		del res['tag_objs']
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")
		
	

@login_required
def insert_reply(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		thread_id = request.POST.get('thread_id')
		group_name = request.POST.get('group_name')
		if thread_id and not group_name:
			group_name = Thread.objects.get(id=thread_id).group.name
		else:
			group_name = group_name.encode('ascii', 'ignore')
		
		orig_subject = request.POST['subject']
		
		if request.POST['subject'][0:4].lower() == "re: ":
			orig_subject = re.sub("\[.*?\]", "", request.POST['subject'][4:]).strip()
		else:
			orig_subject = re.sub("\[.*?\]", "", request.POST['subject']).strip()
		
		msg_text = request.POST['msg_text']
		
		#msg_id = request.POST['msg_id'].encode('ascii', 'ignore')
		msg_id = base64.b64encode(user.email + str(datetime.datetime.now())).lower() + '@' + BASE_URL
		
		original_group = None
		original_group_object = None
		if 'original_group' in request.POST:
			original_group = request.POST['original_group'] + '@' + HOST
			group = Group.objects.get(name=group_name)
			original_group_object = ForwardingList.objects.get(email=original_group, group=group)

		res = engine.main.insert_reply(group_name, 'Re: ' + orig_subject, msg_text, user, user.email, msg_id, forwarding_list=original_group_object, thread_id=thread_id)
		
		if(res['status']):
			
			to_send =  res['recipients']
			post_addr = '%s <%s>' %(group_name, group_name + '@' + HOST)
			
					
			subj_tag = ''
			for tag in res['tags']:
				subj_tag += '[%s]' % tag['name']
			
			subject = 'Re: [%s]%s %s' %(group_name, subj_tag, orig_subject)

			mail = setup_post(user.email,
					subject,	
					group_name)
		
			mail['References'] = msg_id		
			mail['message-id'] = res['msg_id']
			
			mail["In-Reply-To"] = msg_id
			
			g = Group.objects.get(name=group_name)
			t = Thread.objects.get(id=res['thread_id'])
			
			logging.debug('TO LIST: ' + str(to_send))
			
			if len(to_send) > 0:
				
				recips = UserProfile.objects.filter(email__in=to_send)
				membergroups = MemberGroup.objects.filter(group=g, member__in=recips)
				
				followings = Following.objects.filter(thread=t, user__in=recips)
				mutings = Mute.objects.filter(thread=t, user__in=recips)
				
				tag_followings = FollowTag.objects.filter(group=g, tag__in=res['tag_objs'], user__in=recips)
				tag_mutings = MuteTag.objects.filter(group=g, tag__in=res['tag_objs'], user__in=recips)
				
				for recip in recips:
					membergroup = membergroups.filter(member=recip)[0]
					following = followings.filter(user=recip).exists()
					muting = mutings.filter(user=recip).exists()
					tag_following = tag_followings.filter(user=recip)
					tag_muting = tag_mutings.filter(user=recip)

					ps_blurb = html_ps(g, t, res['post_id'], membergroup, following, muting, tag_following, tag_muting, res['tag_objs'], original_list_email=original_group)
					mail.Html = msg_text + ps_blurb	
					
					ps_blurb = plain_ps(g, t, res['post_id'], membergroup, following, muting, tag_following, tag_muting, res['tag_objs'], original_list_email=original_group)
					mail.Body = html2text(msg_text) + ps_blurb
				
					relay_mailer.deliver(mail, To = recip.email)

			fwding_lists = ForwardingList.objects.filter(group=g, can_receive=True)

			for l in fwding_lists:

				# non murmur list, send on as usual
				if HOST not in l.email:
					footer_html = html_forwarded_blurb(g.name, l.email)
					mail.Html = msg_text + footer_html
					footer_plain = plain_forwarded_blurb(g.name, l.email)
					mail.Body = html2text(msg_text) + footer_plain
					relay_mailer.deliver(mail, To = l.email)

				# need to bypass sending email to prevent "loops back to myself" error,
				# so modify request object then recursively call insert_post on it
				else: 
					group_name = l.email.split('@')[0]
					# request.POST is immutable; have to copy, edit, and then reassign
					new_post = request.POST.copy()
					new_post['group_name'] = group_name
					# delete thread_id so message won't go to the thread for the original post
					new_post['thread_id'] = None
					if 'original_group' not in new_post:
						new_post['original_group'] = g.name
					request.POST = new_post
					insert_reply(request)

		del res['tag_objs']
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print sys.exc_info()
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")
	
@render_to(WEBSITE+"/follow_tag.html")
@login_required
def follow_tag_get(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")
		
		tag_name = request.GET.get('tag')
		group_name = request.GET.get('group')
		res = engine.main.follow_tag(tag_name, group_name, user=user)
		
		active_group = load_groups(request, groups, user, group_name=group_name)
		
		return {'res': res, 'type': 'follow', 'user': request.user, 'groups': groups, 'active_group': active_group}
	else:
		return redirect("%s?next=/follow_tag_get?tag=%s&group=%s" % (global_settings.LOGIN_URL, request.GET.get('tag'), request.GET.get('group')))

@render_to(WEBSITE+"/follow_tag.html")
@login_required
def unfollow_tag_get(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")
		
		tag_name = request.GET.get('tag')
		group_name = request.GET.get('group')
		res = engine.main.unfollow_tag(tag_name, group_name, user=user)
		
		active_group = load_groups(request, groups, user, group_name=group_name)
		
		return {'res': res, 'type': 'unfollow', 'user': request.user, 'groups': groups, 'active_group': active_group}
	else:
		return redirect("%s?next=/unfollow_tag_get?tag=%s&group=%s" % (global_settings.LOGIN_URL, request.GET.get('tag'), request.GET.get('group')))

@render_to(WEBSITE+"/follow_tag.html")
@login_required
def mute_tag_get(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")
		
		tag_name = request.GET.get('tag')
		group_name = request.GET.get('group')
		res = engine.main.mute_tag(tag_name, group_name, user=user)
		
		active_group = load_groups(request, groups, user, group_name=group_name)
		
		return {'res': res, 'type': 'mut', 'user': request.user, 'groups': groups, 'active_group': active_group}
	else:
		return redirect("%s?next=/mute_tag_get?tag=%s&group=%s" % (global_settings.LOGIN_URL, request.GET.get('tag'), request.GET.get('group')))

@render_to(WEBSITE+"/follow_tag.html")
@login_required
def unmute_tag_get(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")
		
		tag_name = request.GET.get('tag')
		group_name = request.GET.get('group')
		res = engine.main.unmute_tag(tag_name, group_name, user=user)
		
		active_group = load_groups(request, groups, user, group_name=group_name)
		
		return {'res': res, 'type': 'unmut', 'user': request.user, 'groups': groups, 'active_group': active_group}
	else:
		return redirect("%s?next=/unmute_tag_get?tag=%s&group=%s" % (global_settings.LOGIN_URL, request.GET.get('tag'), request.GET.get('group')))

	

@render_to(WEBSITE+"/follow_thread.html")
@login_required
def follow_thread_get(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")
		
		thread_id = request.GET.get('tid')
		res = engine.main.follow_thread(thread_id, user=user)
		active_group = load_groups(request, groups, user, group_name=res['group_name'])
		
		return {'res': res, 'type': 'follow', 'user': request.user, 'groups': groups, 'active_group': active_group}
	else:
		return redirect(global_settings.LOGIN_URL + "?next=/follow?tid=" + request.GET.get('tid'))

@render_to(WEBSITE+"/follow_thread.html")
@login_required
def unfollow_thread_get(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")
		
		thread_id = request.GET.get('tid')
		res = engine.main.unfollow_thread(thread_id, user=user)
		active_group = load_groups(request, groups, user, group_name=res['group_name'])
		
		return {'res': res, 'type': 'unfollow', 'user': request.user, 'groups': groups, 'active_group': active_group}
	else:
		return redirect(global_settings.LOGIN_URL + "?next=/unfollow?tid=" + request.GET.get('tid'))
	
@render_to(WEBSITE+"/follow_thread.html")
@login_required
def mute_thread_get(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")
		
		thread_id = request.GET.get('tid')
		res = engine.main.mute_thread(thread_id, user=user)
		active_group = load_groups(request, groups, user, group_name=res['group_name'])
		
		return {'res': res, 'type': 'mut', 'user': request.user, 'groups': groups, 'active_group': active_group}
	else:
		return redirect(global_settings.LOGIN_URL + "?next=/mute?tid=" + request.GET.get('tid'))

@render_to(WEBSITE+"/follow_thread.html")
@login_required
def unmute_thread_get(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")

		thread_id = request.GET.get('tid')
		res = engine.main.unmute_thread(thread_id, user=user)
		active_group = load_groups(request, groups, user, group_name=res['group_name'])
		
		return {'res': res, 'type': 'unmut', 'user': request.user, 'groups': groups, 'active_group': active_group}
	else:
		return redirect(global_settings.LOGIN_URL + "?next=/unmute?tid=" + request.GET.get('tid'))


@login_required
def upvote(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.upvote(request.POST['post_id'], user=user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")
	
@login_required
def unupvote(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.unupvote(request.POST['post_id'], user=user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")


@render_to(WEBSITE+'/subscribe.html')
@login_required
def unsubscribe_get(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.unsubscribe_group(request.GET.get('group_name'), user)
		groups = Group.objects.filter(membergroup__member=user).values("name")
		active_group = {'name':'No Groups Yet'}
		if len(groups) > 0:
			active_group = load_groups(request, groups, user, group_name=groups[0]['name'])
		return {'res':res, 'type': 'unsubscribed from', 'user': request.user, 'group_name' : request.GET.get('group_name'),
		'groups' : groups, 'active_group': active_group}
	else:
		return redirect(global_settings.LOGIN_URL + '?next=/unsubscribe_get?group_name=' + request.GET.get('group_name'))

@render_to(WEBSITE+'/subscribe.html')
def subscribe_get(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		group_name = request.GET.get('group_name')
		res = engine.main.subscribe_group(group_name, user)
		groups = Group.objects.filter(membergroup__member=user).values("name")
		if res['status']:
			active_group = load_groups(request, groups, user, group_name=group_name)
		else:
			active_group = {'name':'No Groups Yet'}
			if len(groups) > 0:
				active_group = load_groups(request, groups, user, group_name=groups[0]['name'])
		return {'res':res, 'type': 'subscribed to', 'user': request.user, 'groups': groups,
				'active_group': active_group, 'group_name' : group_name,
				'email': request.user.email}
	else:
		if request.GET.get('email'):
			email = request.GET.get('email')
			group_name = request.GET.get('group_name')
			res = engine.main.add_members(group_name, email, None)
			return {'res':res, 'type': 'subscribed to', 'email': email, 'group_name' : group_name}
		else:
			return redirect(global_settings.LOGIN_URL + '?next=/subscribe_get?group_name=' + request.GET.get('group_name'))

@render_to(WEBSITE+"/upvote.html")
@login_required
def upvote_get(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")
		post_id = request.GET.get('post_id')
		res = engine.main.upvote(post_id, user=user)
		active_group = load_groups(request, groups, user, group_name=res['group_name'])
		
		return {'res': res, 'type': 'upvoted', 'user': request.user, 'groups': groups, 'active_group': active_group}
	else:
		return redirect(global_settings.LOGIN_URL + "?next=/upvote_get?post_id=" + request.GET.get('post_id'))
	
@render_to(WEBSITE+"/upvote.html")
@login_required
def unupvote_get(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")

		post_id = request.GET.get('post_id')
		res = engine.main.unupvote(post_id, user=user)
		active_group = load_groups(request, groups, user, group_name=res['group_name'])
		
		return {'res': res, 'type': 'undid your upvote of', 'user': request.user, 'groups': groups, 'active_group': active_group}
	else:
		return redirect(global_settings.LOGIN_URL + "?next=/unupvote_get?post_id=" + request.GET.get('post_id'))

# TODO: make a page for this. 
@login_required
def blacklist_get(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")
		group_name = request.GET.get('group_name')
		sender_email = request.GET.get('sender_email')
		res = engine.main.update_blacklist_whitelist(user, group_name, sender_email, False, True)
		return HttpResponse(json.dumps(res), content_type="application/json")
	else:
		# TODO: send them to login page and redirect
		error = 'You are not logged in.'
		return HttpResponse(error, content_type="application/json")

# TODO: make a page for this. 
@login_required
def whitelist_get(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		groups = Group.objects.filter(membergroup__member=user).values("name")
		group_name = request.GET.get('group_name')
		sender_email = request.GET.get('sender_email')
		res = engine.main.update_blacklist_whitelist(user, group_name, sender_email, True, False)
		return HttpResponse(json.dumps(res), content_type="application/json")
	else:
		# TODO: send them to login page and redirect
		error = 'You are not logged in.'
		return HttpResponse(error, content_type="application/json")

@login_required
def approve_get(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		group_name = request.GET.get('group_name')
		post_id = request.GET.get('post_id')
		res = engine.main.update_post_status(user, group_name, post_id, 'A')
		return HttpResponse(json.dumps(res), content_type="application/json")
	else:
		# TODO: send them to login page and redirect
		error = 'You are not logged in.'
		return HttpResponse(error, content_type="application/json")

@login_required
def reject_get(request):
	if request.user.is_authenticated():
		user = get_object_or_404(UserProfile, email=request.user.email)
		group_name = request.GET.get('group_name')
		post_id = request.GET.get('post_id')
		res = engine.main.update_post_status(user, group_name, post_id, 'R')
		return HttpResponse(json.dumps(res), content_type="application/json")
	else:
		# TODO: send them to login page and redirect
		error = 'You are not logged in.'
		return HttpResponse(error, content_type="application/json")

@login_required
def follow_thread(request):
	try:
		if request.user.is_authenticated():
			user = get_object_or_404(UserProfile, email=request.user.email)
			res = engine.main.follow_thread(request.POST['thread_id'], user=user)
			return HttpResponse(json.dumps(res), content_type="application/json")
		else:
			thread = request.POST['thread_id']
			return HttpResponse(json.dumps({'redirect': True, 
										'url': global_settings.LOGIN_URL + "?next=/thread?tid=" + thread}), 
										content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def unfollow_thread(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.unfollow_thread(request.POST['thread_id'], user=user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def follow_tag(request):
	try:
		if request.user.is_authenticated():
			user = get_object_or_404(UserProfile, email=request.user.email)
			res = engine.main.follow_tag(request.POST['tag_name'], request.POST['group_name'], user=user)
			return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def unfollow_tag(request):
	try:
		if request.user.is_authenticated():
			user = get_object_or_404(UserProfile, email=request.user.email)
			res = engine.main.unfollow_tag(request.POST['tag_name'], request.POST['group_name'], user=user)
			return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def mute_tag(request):
	try:
		if request.user.is_authenticated():
			user = get_object_or_404(UserProfile, email=request.user.email)
			res = engine.main.mute_tag(request.POST['tag_name'], request.POST['group_name'], user=user)
			return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def unmute_tag(request):
	try:
		if request.user.is_authenticated():
			user = get_object_or_404(UserProfile, email=request.user.email)
			res = engine.main.unmute_tag(request.POST['tag_name'], request.POST['group_name'], user=user)
			return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def mute_thread(request):
	try:
		if request.user.is_authenticated():
			user = get_object_or_404(UserProfile, email=request.user.email)
			res = engine.main.mute_thread(request.POST['thread_id'], user=user)
			return HttpResponse(json.dumps(res), content_type="application/json")
		else:
			thread = request.POST['thread_id']
			return HttpResponse(json.dumps({'redirect': True, 
										'url': global_settings.LOGIN_URL + "?next=/thread?tid=" + thread}), 
										content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def unmute_thread(request):
	try:
		user = get_object_or_404(UserProfile, email=request.user.email)
		res = engine.main.unmute_thread(request.POST['thread_id'], user=user)
		return HttpResponse(json.dumps(res), content_type="application/json")
	except Exception, e:
		print e
		logging.debug(e)
		return HttpResponse(request_error, content_type="application/json")

@login_required
def murmur_acct(request, acct_func=None, template_name=None):
	user = get_object_or_404(UserProfile, email=request.user.email)
	groups = Group.objects.filter(membergroup__member=user).values("name")
	active_group = load_groups(request, groups, user)
	if request.path_info == "/accounts/password/change/": template=WEBSITE+"/registration/password_change_form.html"
	elif request.path_info == "/password/change/done/": template=WEBSITE+"/registration/password_change_done.html"
	elif request.path_info == "/accounts/password/reset/": template=WEBSITE+"/registration/password_reset_form.html"
	elif request.path_info == "/password/reset/done/": template=WEBSITE+"/registration/password_reset_done.html"
	elif request.path_info == "/password/reset/complete/": template=WEBSITE+"/registration/password_reset_complete.html"
	else: template=WEBSITE+"/registration/password_reset_confirm.html"
	return acct_func(request, template_name=template, extra_context={'active_group': active_group, 'groups': groups, 'user': request.user})

@login_required
def serve_attachment(request, hash_filename):
	if Attachment.objects.filter(hash_filename=hash_filename):
		if request.user.is_authenticated():
			user = get_object_or_404(UserProfile, email=request.user.email)
			user_groups = Group.objects.filter(membergroup__member=user).values("name")
			msg_id = Attachment.objects.filter(hash_filename=hash_filename)[0].msg_id
			authorized_group = Post.objects.filter(msg_id=msg_id)[0].group[0].name
			if authorized_group in user_groups:
				s3 = S3Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, is_secure=True)
				filename = Attachment.objects.filter(hash_filename=hash_filename)[0].true_filename
				filepath = hash_filename + "/" + filename
				temporary_auth_url = s3.generate_url(60, 'GET', bucket=AWS_STORAGE_BUCKET_NAME, key=filepath)
				return HttpResponseRedirect(temporary_auth_url)
	else:
		return HttpResponseRedirect('/404')
