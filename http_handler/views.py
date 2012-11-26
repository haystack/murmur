from django.http import *

'''
@author: Anant Bhardwaj
@date: Nov 9, 2012

MailX Web Interface Handler
'''

def index(request):
	request.session.set_test_cookie()
	return HttpResponseRedirect('browser/')