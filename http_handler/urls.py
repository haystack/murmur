from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
     url(r'^$', 'browser.views.index'),
	 url(r'^posts', 'browser.views.posts'),
	 url(r'^groups', 'browser.views.groups'),
	 
	 url(r'^list_groups', 'browser.views.list_groups'),
	 url(r'^create_group', 'browser.views.create_group'),
	 url(r'^activate_group', 'browser.views.activate_group'),
	 url(r'^deactivate_group', 'browser.views.deactivate_group'),
	 url(r'^subscribe_group', 'browser.views.subscribe_group'),
	 url(r'^unsubscribe_group', 'browser.views.unsubscribe_group'),
	 url(r'^group_info', 'browser.views.group_info'),
	 
	 url(r'^list_posts', 'browser.views.list_posts'),
	 url(r'^load_post', 'browser.views.load_post'),
	 url(r'^insert_post', 'browser.views.insert_post'), 
	 url(r'^insert_reply', 'browser.views.insert_reply'),
	 url(r'^follow_thread', 'browser.views.follow_thread'),
	 url(r'^unfollow_thread', 'browser.views.unfollow_thread'),
	 
	 url(r'^login', 'browser.views.login'),
	 url(r'^logout', 'browser.views.logout'),
)
