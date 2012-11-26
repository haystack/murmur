from django.http import *
'''
@author: Anant Bhardwaj
@date: Nov 9, 2012

MailX Web Interface Handler
'''

def index(request):
	return HttpResponseRedirect('/mailx/browser/')