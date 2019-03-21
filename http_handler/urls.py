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

    url(r'^thread$', 'browser.views.thread'),

    url(r'^create_new_group', 'browser.views.create_group_view'), 
    url(r'^create_group', 'browser.views.create_group'),
    url(r'^delete_group', 'browser.views.delete_group'),

    url(r'^groups/(?P<group_name>[\w-]+)/edit_group_info', 'browser.views.edit_group_info_view'),
    url(r'^edit_group_info', 'browser.views.edit_group_info'),
    url(r'^group_info', 'browser.views.group_info'),
    url(r'^groups/(?P<group_name>[\w-]+)$', 'browser.views.group_page'),

    url(r'^groups/(?P<group_name>[\w-]+)/add_members', 'browser.views.add_members_view'),
    url(r'^add_members', 'browser.views.add_members'),
    url(r'^edit_members', 'browser.views.edit_members'),

    url(r'^unsubscribe_group', 'browser.views.unsubscribe_group'),
    url(r'^subscribe_group', 'browser.views.subscribe_group'),

    url(r'^my_group_list', 'browser.views.my_group_list'),

    url(r'^edit_group_settings', 'browser.views.edit_group_settings'),
    url(r'^group_settings', 'browser.views.get_group_settings'),
    url(r'^groups/(?P<group_name>[\w-]+)/edit_my_settings', 'browser.views.my_group_settings_view'),

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
                       
    url(r'^attachment/(?P<hash_filename>[0-9A-Za-z_]+)', 'browser.views.serve_attachment'),

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

    url(r'^subscribe/confirm/(?P<token>.+)$', 'browser.views.subscribe_confirm'),

    url(r'^activate_group', 'browser.views.activate_group'),
    url(r'^deactivate_group', 'browser.views.deactivate_group'),

    # mailbot
    url(r'^editor', 'browser.views.login_imap_view'),
    url(r'^docs', 'browser.views.docs_view'),
    url(r'^login_imap', 'browser.views.login_imap'),
    url(r'^remove_rule', 'browser.views.remove_rule'),
    url(r'^run_mailbot', 'browser.views.run_mailbot'),
    url(r'^save_shortcut', 'browser.views.save_shortcut'),
                    
    url(r'^delete_mailbot_mode', 'browser.views.delete_mailbot_mode'),
    url(r'^fetch_execution_log', 'browser.views.fetch_execution_log'),
    url(r'^folder_recent_messages', 'browser.views.folder_recent_messages'),
    )

# murmur-only patterns
if WEBSITE == 'murmur':
    new_patterns = [
                    url(r'^about', 'browser.views.about'),
                    url(r'^posts$', 'browser.views.posts'),
   
                    url(r'^unsubscribe_get', 'browser.views.unsubscribe_get'),
                    url(r'^subscribe_get', 'browser.views.subscribe_get'),

                    url(r'^post_list', 'browser.views.post_list'),
                    url(r'^pub_group_list', 'browser.views.pub_group_list'),
                    url(r'^group_list', 'browser.views.group_list'),
                    url(r'^groups/(?P<group_name>[\w-]+)/add_list', 'browser.views.add_list_view'),
                    url(r'^groups/(?P<group_name>[\w-]+)/create_post', 'browser.views.my_group_create_post_view'),
                    url(r'^my_groups', 'browser.views.my_groups'),
                    url(r'^list_my_groups', 'browser.views.list_my_groups'), 

                    url(r'^load_post', 'browser.views.load_post'),
                    url(r'^load_thread', 'browser.views.load_thread'),

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

                    url(r'^add_list', 'browser.views.add_list'),
                    url(r'^delete_list', 'browser.views.delete_list'),
                    
                    url(r'^adjust_list_can_post', 'browser.views.adjust_list_can_post'),
                    url(r'^adjust_list_can_receive', 'browser.views.adjust_list_can_receive'),

                    url(r'^groups/(?P<group_name>[\w-]+)/add_donotsend', 'browser.views.add_dissimulate_view'),
                    url(r'^edit_donotsend', 'browser.views.edit_donotsend'),
                    url(r'^donotsend_list', 'browser.views.donotsend_list'),
                    ]

    urlpatterns.extend(new_patterns)

# squadbox-only patterns
elif WEBSITE == 'squadbox': 

    new_patterns = [
                    url(r'^mod_queue/(?P<group_name>[\w-]+)', 'browser.views.mod_queue'),

                    # url(r'^approve_get', 'browser.views.approve_get'),
                    # url(r'^reject_get', 'browser.views.reject_get'),

                    url(r'^approve_post', 'browser.views.approve_post'),
                    url(r'^reject_post', 'browser.views.reject_post'),

                    url(r'^delete_posts', 'browser.views.delete_posts'),
                    url(r'^delete_post', 'browser.views.delete_post'),

                    url(r'^whitelist_get', 'browser.views.whitelist_get'),
                    url(r'^whitelist', 'browser.views.whitelist'),
                    url(r'^groups/(?P<group_name>[\w-]+)/add_whitelist', 'browser.views.add_whitelist_view'),

                    url(r'^unblacklist_unwhitelist', 'browser.views.unblacklist_unwhitelist'),

                    url(r'^blacklist_get', 'browser.views.blacklist_get'),
                    url(r'^blacklist', 'browser.views.blacklist'),
                    url(r'^groups/(?P<group_name>[\w-]+)/add_blacklist', 'browser.views.add_blacklist_view'),

                    url(r'^groups/(?P<group_name>[\w-]+)/rejected', 'browser.views.rejected'),
                    url(r'^rejected_thread$', 'browser.views.rejected_thread'),

                    url(r'^moderate_user_for_thread_get', 'browser.views.moderate_user_for_thread_get'),
                    ]

    urlpatterns.extend(new_patterns)
