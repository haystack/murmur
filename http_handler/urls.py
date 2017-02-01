from django.conf.urls import patterns, include, url
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView
from browser.views import *
from http_handler.settings import WEBSITE
from registration.backends.default.views import ActivationView
from registration.forms import MurmurPasswordResetForm
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

website_context = {'website' : WEBSITE}

# shared URL patterns 
urlpatterns = patterns('',

    url(r'^$', 'browser.views.index'),
    url(r'^lamson_status', 'browser.views.lamson_status'),
    url(r'^settings', 'browser.views.settings'),
    url(r'^404', 'browser.views.error'),

    url(r'^create_new_group', 'browser.views.create_group_view'), 
    url(r'^groups/(?P<group_name>[\w-]+)$', 'browser.views.group_page'),
    url(r'^groups/(?P<group_name>[\w-]+)/add_members', 'browser.views.add_members_view'),
    url(r'^add_members', 'browser.views.add_members'),
                       
   url(r'^gmail_setup/', include('gmail_setup.urls', namespace="oauth2")),
     
    #override the registration default urls - bug with django 1.6
    url(r'^accounts/password/change/$',
                    murmur_acct,
                    {'acct_func': auth_views.password_change, 'template_name': 'registration/password_change_form.html'},
                    name='password_change',
                    ),
    url(r'^accounts/password/change/done/$',
                    murmur_acct,
                    {'acct_func': auth_views.password_change_done, 'template_name': 'registration/password_change_done.html'},
                    name='password_change_done',
                    ),
    url(r'^accounts/password/reset/$',
                    auth_views.password_reset,
                    {'password_reset_form' : MurmurPasswordResetForm,
                    'extra_context' : website_context},
                    name='password_reset'),
    url(r'^accounts/password/reset/done/$',
                    auth_views.password_reset_done,
                    {'extra_context' : website_context},
                    name='password_reset_done'),
    url(r'^accounts/password/reset/complete/$',
                    auth_views.password_reset_complete,
                    {'extra_context' : website_context},
                    name='password_reset_complete'),
    url(r'^accounts/password/reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
                    auth_views.password_reset_confirm,
                    {'extra_context' : website_context},
                    name='password_reset_confirm'),

    url(r'^accounts/activate/complete/$',
       TemplateView.as_view(template_name='registration/activation_complete.html'),
       website_context,
       name='registration_activation_complete',
    ),

    url(r'^accounts/activate/(?P<activation_key>\w+)/$',
        ActivationView.as_view(),
        name='registration_activate',
    ),

    url(r'^accounts/register/complete/$',
        TemplateView.as_view(template_name='registration/registration_complete.html'),
        website_context,
        name='registration_complete',
    ),

    url(r'^accounts/', include('registration.backends.default.urls')),
    )

# murmur-only patterns
if WEBSITE == 'murmur':
    new_patterns = [
                    url(r'^about', 'browser.views.about'),
                    url(r'^posts$', 'browser.views.posts'),
                    url(r'^thread$', 'browser.views.thread'),
                    url(r'^post_list', 'browser.views.post_list'),
                    url(r'^pub_group_list', 'browser.views.pub_group_list'),
                    url(r'^group_list', 'browser.views.group_list'),
                    url(r'^group_info', 'browser.views.group_info'),
                    url(r'^groups/(?P<group_name>[\w-]+)/add_list', 'browser.views.add_list_view'),
                    url(r'^groups/(?P<group_name>[\w-]+)/create_post', 'browser.views.my_group_create_post_view'),
                    url(r'^activate_group', 'browser.views.activate_group'),
                    url(r'^deactivate_group', 'browser.views.deactivate_group'),
                    url(r'^subscribe_group', 'browser.views.subscribe_group'),

                    # TODO: make all of these work/customize for squadbox
                    url(r'^groups/(?P<group_name>[\w-]+)/edit_my_settings', 'browser.views.my_group_settings_view'),
                    url(r'^groups/(?P<group_name>[\w-]+)/edit_group_info', 'browser.views.edit_group_info_view'),
                    url(r'^edit_group_info', 'browser.views.edit_group_info'),
                    url(r'^delete_group', 'browser.views.delete_group'),
                    url(r'^my_groups', 'browser.views.my_groups'),
                    url(r'^my_group_list', 'browser.views.my_group_list'),
                    url(r'^group_settings', 'browser.views.get_group_settings'),
                    url(r'^unsubscribe_group', 'browser.views.unsubscribe_group'),
                    url(r'^create_group', 'browser.views.create_group'),
                    url(r'^edit_members', 'browser.views.edit_members'),
                    url(r'^load_post', 'browser.views.load_post'),
                    url(r'^list_my_groups', 'browser.views.list_my_groups'), 
                    url(r'^edit_group_settings', 'browser.views.edit_group_settings'),
                    # end TODO

                    url(r'^list_posts', 'browser.views.list_posts'),
                    url(r'^refresh_posts', 'browser.views.refresh_posts'),
                    
                    url(r'^insert_post', 'browser.views.insert_post'), 
                    url(r'^insert_reply', 'browser.views.insert_reply'),
                     
                    url(r'^upvote_get', 'browser.views.upvote_get'),
                    url(r'^unupvote_get', 'browser.views.unupvote_get'),

                    url(r'^upvote', 'browser.views.upvote'),
                    url(r'^unupvote', 'browser.views.unupvote'),
                     
                    url(r'^follow_tag_get', 'browser.views.follow_tag_get'),
                    url(r'^unfollow_tag_get', 'browser.views.unfollow_tag_get'),
                     
                    url(r'^mute_tag_get', 'browser.views.mute_tag_get'),
                    url(r'^unmute_tag_get', 'browser.views.unmute_tag_get'),
                     
                    url(r'^follow_tag', 'browser.views.follow_tag'),
                    url(r'^unfollow_tag', 'browser.views.unfollow_tag'),
                     
                    url(r'^mute_tag', 'browser.views.mute_tag'),
                    url(r'^unmute_tag', 'browser.views.unmute_tag'),
                     
                    url(r'^follow_thread', 'browser.views.follow_thread'),
                    url(r'^unfollow_thread', 'browser.views.unfollow_thread'),
                     
                    url(r'^mute_thread', 'browser.views.mute_thread'),
                    url(r'^unmute_thread', 'browser.views.unmute_thread'),
                     
                    url(r'^follow', 'browser.views.follow_thread_get'),
                    url(r'^unfollow', 'browser.views.unfollow_thread_get'),

                    url(r'^mute', 'browser.views.mute_thread_get'),
                    url(r'^unmute', 'browser.views.unmute_thread_get'),
                     
                    url(r'^unsubscribe_get', 'browser.views.unsubscribe_get'),
                    url(r'^subscribe_get', 'browser.views.subscribe_get'),

                    url(r'^add_list', 'browser.views.add_list'),
                    url(r'^delete_list', 'browser.views.delete_list'),
                    
                    url(r'^adjust_list_can_post', 'browser.views.adjust_list_can_post'),
                    url(r'^adjust_list_can_receive', 'browser.views.adjust_list_can_receive'),


                    ]

    urlpatterns.extend(new_patterns)

# squadbox-only patterns
elif WEBSITE == 'squadbox': 

    new_patterns = [
                    url(r'^dashboard', 'browser.views.dashboard'),
                    ]

    urlpatterns.extend(new_patterns)
