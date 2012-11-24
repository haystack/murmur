from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
     url(r'^login', 'account.views.login'),
	 url(r'^register', 'account.views.register'),
	 url(r'^logout', 'account.views.logout'),
)