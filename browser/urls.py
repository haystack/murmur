from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
     url(r'^$', 'browser.views.index'),
	 url(r'^ajax/msg_list/', 'browser.ajax.msg_list'),
	 url(r'^ajax/msg_thread/', 'brwser.ajax.msg_thread'),

)
