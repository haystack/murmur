from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
     url(r'^login', 'django.contrib.auth.views.login', {'template_name':'login.html'}),
	 url(r'^logout', 'http_handler.views.logout'),
)