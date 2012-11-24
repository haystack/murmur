from django.http import *
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

'''
@author: Anant Bhardwaj
@date: Nov 9, 2012
'''
@login_required(login_url='/login/')
def index(request):
	return render_to_response("index.html")
	

def logout(request):
	ajax.logout(request)
	return HttpResponseRedirect('/logout')
