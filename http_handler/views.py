from django.http import *

'''
@author: Anant Bhardwaj
@date: Nov 9, 2012

MailX Web Interface Handler
'''
request_error = json.dumps({'code': msg_code['REQUEST_ERROR'],'status':False})

def index(request):
	return HttpResponseRedirect('browser/')