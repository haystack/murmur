from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
     url(r'^$', 'browser.views.index'),
	 url(r'^index', 'browser.views.index'),
	 url(r'^settings', 'browser.views.settings'),
	 url(r'^list_groups', 'browser.views.list_groups'),
	 url(r'^create_group', 'browser.views.create_group'),
	 url(r'^activate_group', 'browser.views.activate_group'),
	 url(r'^deactivate_group', 'browser.views.deactivate_group'),
	 url(r'^subscribe_group', 'browser.views.subscribe_group'),
	 url(r'^unsubscribe_group', 'browser.views.unsubscribe_group'),
	 url(r'^group_info', 'browser.views.group_info'),
	 url(r'^insert_post', 'browser.views.insert_post'), 
	 url(r'^insert_reply', 'browser.views.insert_reply'),
	 url(r'^follow_post', 'browser.views.follow_post'),
	 url(r'^unfollow_post', 'browser.views.unfollow_post'),
	 
	 url(r'^login', 'browser.views.login'),
	 url(r'^logout', 'browser.views.logout'),
)
