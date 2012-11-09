from django.http import *
from django.shortcuts import render_to_response

def index(request):
	return HttpResponse("OK")

	

