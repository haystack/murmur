from django.http import *
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout


'''
@author: Anant Bhardwaj
@date: Nov 9, 2012

MailX Browser
'''


def index(request):
	return render_to_response("index.html")




	