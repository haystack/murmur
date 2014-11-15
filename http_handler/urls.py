from django.conf.urls import patterns, include, url
from django.contrib.auth import views as auth_views
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
     url(r'^$', 'browser.views.index'),
     url(r'^settings', 'browser.views.settings'),
	 url(r'^posts$', 'browser.views.posts'),
	 url(r'^my_groups', 'browser.views.my_groups'),
     url(r'^group_list', 'browser.views.group_list'),
     url(r'^groups/(?P<group_name>[\w-]+)/add_members', 'browser.views.add_members_view'),
     url(r'^groups/(?P<group_name>[\w-]+)', 'browser.views.group_page'),
     url(r'^404', 'browser.views.error'),
	 
	 url(r'^list_my_groups', 'browser.views.list_my_groups'),
	 url(r'^create_group', 'browser.views.create_group'),
     
	 url(r'^activate_group', 'browser.views.activate_group'),
	 url(r'^deactivate_group', 'browser.views.deactivate_group'),
	 url(r'^subscribe_group', 'browser.views.subscribe_group'),
	 url(r'^unsubscribe_group', 'browser.views.unsubscribe_group'),
	 url(r'^group_info', 'browser.views.group_info'),
     url(r'^add_members', 'browser.views.add_members'),
	 
	 url(r'^list_posts', 'browser.views.list_posts'),
	 url(r'^refresh_posts', 'browser.views.refresh_posts'),
	 url(r'^load_post', 'browser.views.load_post'),
	 url(r'^insert_post', 'browser.views.insert_post'), 
	 url(r'^insert_reply', 'browser.views.insert_reply'),
	 url(r'^follow_thread', 'browser.views.follow_thread'),
	 url(r'^unfollow_thread', 'browser.views.unfollow_thread'),
     
    #override the registration default urls - bug with django 1.6
      url(r'^password/change/$',
                    auth_views.password_change,
                    name='password_change'),
      url(r'^password/change/done/$',
                    auth_views.password_change_done,
                    name='password_change_done'),
      url(r'^password/reset/$',
                    auth_views.password_reset,
                    name='password_reset'),
      url(r'^password/reset/done/$',
                    auth_views.password_reset_done,
                    name='password_reset_done'),
      url(r'^password/reset/complete/$',
                    auth_views.password_reset_complete,
                    name='password_reset_complete'),
      url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
                    auth_views.password_reset_confirm,
                    name='password_reset_confirm'),
                       
     (r'^accounts/', include('registration.backends.default.urls')),

)
