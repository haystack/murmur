from django.http import *
from django.shortcuts import render_to_response

'''
@author: Anant Bhardwaj
@date: Nov 9, 2012
'''

def index(request):
	return render_to_response("index.html")
