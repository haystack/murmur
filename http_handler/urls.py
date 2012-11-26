from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
     url(r'^$', 'http_handler.views.index'),
	 (r'^account/', include('account.urls')),
	 (r'^browser/', include('browser.urls')),
	 url(r'^list_groups', 'http_handler.views.list_groups'),
	 url(r'^create_group', 'http_handler.views.create_group'),
	 url(r'^activate_group', 'http_handler.views.activate_group'),
	 url(r'^deactivate_group', 'http_handler.views.deactivate_group'),
	 url(r'^subscribe_group', 'http_handler.views.subscribe_group'),
	 url(r'^unsubscribe_group', 'http_handler.views.unsubscribe_group'),
	 url(r'^group_info', 'http_handler.views.group_info'),
	 url(r'^insert_post', 'http_handler.views.insert_post'), 
	 url(r'^insert_reply', 'http_handler.views.insert_reply'),
	 url(r'^follow_post', 'http_handler.views.follow_post'),
	 url(r'^unfollow_post', 'http_handler.views.unfollow_post'),
)