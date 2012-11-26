from django.http import *
from django.core.context_processors import csrf
'''
@author: Anant Bhardwaj
@date: Nov 9, 2012

MailX Web Interface Handler
'''

def index(request):
	context = {}
	context.update(csrf(request))
	return HttpResponseRedirect('browser/', context)