from django.http import *
from django.shortcuts import render_to_response
from django.contrib.auth.views import login as auth_login
from django.contrib.auth.views import logout as auth_logout

'''
@author: Anant Bhardwaj
@date: Nov 9, 2012
'''

def login(request, template_name='login.html'):
	return auth_login(request, template_name = template_name)

def register(request, template_name='register.html'):
	return render_to_response(template_name)

def logout(request):
	auth_logout(request)
	return HttpResponseRedirect('/account/login')
