from django.conf.urls import include, url
from django.urls import reverse_lazy
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordChangeView,
    PasswordChangeDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.views.generic.base import TemplateView
from browser.views import *
from browser import views
from http_handler.settings import WEBSITE
from registration.backends.default.views import ActivationView
from registration.forms import MurmurPasswordResetForm
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

website_context = {'website' : WEBSITE}

#shared URL patterns 
urlpatterns = [
    url(r'^$', views.index),
    url(r'^lamson_status', views.lamson_status),
    url(r'^settings', views.settings),
    url(r'^404', views.error),

    url(r'^thread$', views.thread),

    url(r'^create_new_group', views.create_group_view), 
    url(r'^create_group', views.create_group),
    url(r'^delete_group', views.delete_group),

    url(r'^groups/(?P<group_name>[\w-]+)/edit_group_info', views.edit_group_info_view),
    url(r'^edit_group_info', views.edit_group_info),
    url(r'^group_info', views.group_info),
    url(r'^groups/(?P<group_name>[\w-]+)$', views.group_page),

    url(r'^groups/(?P<group_name>[\w-]+)/add_members', views.add_members_view),
    url(r'^add_members', views.add_members),
    url(r'^edit_members', views.edit_members),

    url(r'^unsubscribe_group', views.unsubscribe_group),
    url(r'^subscribe_group', views.subscribe_group),

    url(r'^my_group_list', views.my_group_list),

    url(r'^edit_group_settings', views.edit_group_settings),
    url(r'^group_settings', views.get_group_settings),
    url(r'^groups/(?P<group_name>[\w-]+)/edit_my_settings', views.my_group_settings_view),

    url(r'^gmail_setup/', include('gmail_setup.urls', namespace="oauth2")),

    url(r'^accounts/login/$', LoginView.as_view(template_name='registration/login.html', 
            extra_context=website_context), 
            name='login'),
    url(r'^accounts/logout/$', LogoutView.as_view(template_name='registration/logout.html', 
            extra_context=website_context, next_page=reverse_lazy('login')), 
            name='logout'),
    url(r'^accounts/password_change/$', PasswordChangeView.as_view(template_name='registration/password_change_form.html',
            extra_context=website_context),  
            name='password_change'),
    url(r'^accounts/password_change/done/$', PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html', 
            extra_context=website_context), 
            name='password_change_done'),
    url(r'^accounts/password_reset/$', PasswordResetView.as_view(form_class=MurmurPasswordResetForm, 
            extra_context=website_context),
            name='password_reset'),
    url(r'^accounts/password_reset/done/$', PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html",
            extra_context=website_context), 
            name='password_reset_done'),
    url(r'^accounts/reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html",
            extra_context=website_context), 
            name='password_reset_confirm'),
    url(r'^accounts/rest/done/$', PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html",
            extra_context=website_context),  
            name='password_reset_complete'),

                       
    url(r'^attachment/(?P<hash_filename>[0-9A-Za-z_]+)', views.serve_attachment),

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

    url(r'^subscribe/confirm/(?P<token>.+)$', views.subscribe_confirm),

    url(r'^activate_group', views.activate_group),
    url(r'^deactivate_group', views.deactivate_group),
]

# murmur-only patterns
if WEBSITE == 'murmur':
    new_patterns = [
        url(r'^about', views.about),
        url(r'^posts$', views.post_list),

        url(r'^unsubscribe_get', views.unsubscribe_get),
        url(r'^subscribe_get', views.subscribe_get),

        url(r'^post_list', views.post_list),
        url(r'^pub_group_list', views.pub_group_list),
        url(r'^group_list', views.group_list),
        url(r'^groups/(?P<group_name>[\w-]+)/add_list', views.add_list_view),
        url(r'^groups/(?P<group_name>[\w-]+)/create_post', views.my_group_create_post_view),
        url(r'^my_groups', views.my_groups),
        url(r'^list_my_groups', views.list_my_groups), 

        url(r'^load_post', views.load_post),
        url(r'^load_thread', views.load_thread),

        url(r'^list_posts', views.list_posts),
        url(r'^refresh_posts', views.refresh_posts),
        
        url(r'^insert_post', views.insert_post), 
        url(r'^insert_reply', views.insert_reply),
            
        url(r'^upvote_get', views.upvote_get),
        url(r'^unupvote_get', views.unupvote_get),

        url(r'^upvote', views.upvote),
        url(r'^unupvote', views.unupvote),
            
        url(r'^follow_tag_get', views.follow_tag_get),
        url(r'^unfollow_tag_get', views.unfollow_tag_get),
            
        url(r'^mute_tag_get', views.mute_tag_get),
        url(r'^unmute_tag_get', views.unmute_tag_get),
            
        url(r'^follow_tag', views.follow_tag),
        url(r'^unfollow_tag', views.unfollow_tag),
            
        url(r'^mute_tag', views.mute_tag),
        url(r'^unmute_tag', views.unmute_tag),
            
        url(r'^follow_thread', views.follow_thread),
        url(r'^unfollow_thread', views.unfollow_thread),
            
        url(r'^mute_thread', views.mute_thread),
        url(r'^unmute_thread', views.unmute_thread),
            
        url(r'^follow', views.follow_thread_get),
        url(r'^unfollow', views.unfollow_thread_get),

        url(r'^mute', views.mute_thread_get),
        url(r'^unmute', views.unmute_thread_get),

        url(r'^add_list', views.add_list),
        url(r'^delete_list', views.delete_list),
        
        url(r'^adjust_list_can_post', views.adjust_list_can_post),
        url(r'^adjust_list_can_receive', views.adjust_list_can_receive),

        url(r'^login_email', views.login_imap_view),
        url(r'^login_imap', views.login_imap),
        url(r'^groups/(?P<group_name>[\w-]+)/add_donotsend', views.add_dissimulate_view),
        url(r'^edit_donotsend', views.edit_donotsend),
        url(r'^donotsend_list', views.donotsend_list),
    ]

    urlpatterns.extend(new_patterns)

# squadbox-only patterns
elif WEBSITE == 'squadbox': 

    new_patterns = [
        url(r'^mod_queue/(?P<group_name>[\w-]+)', views.mod_queue),

        # url(r'^approve_get', 'browser.views.approve_get'),
        # url(r'^reject_get', 'browser.views.reject_get'),

        url(r'^approve_post', views.approve_post),
        url(r'^reject_post', views.reject_post),

        url(r'^delete_posts', views.delete_posts),
        url(r'^delete_post', views.delete_post),

        url(r'^whitelist_get', views.whitelist_get),
        url(r'^whitelist', views.whitelist),
        url(r'^groups/(?P<group_name>[\w-]+)/add_whitelist', views.add_whitelist_view),

        url(r'^unblacklist_unwhitelist', views.unblacklist_unwhitelist),

        url(r'^blacklist_get', views.blacklist_get),
        url(r'^blacklist', views.blacklist),
        url(r'^groups/(?P<group_name>[\w-]+)/add_blacklist', views.add_blacklist_view),

        url(r'^groups/(?P<group_name>[\w-]+)/rejected', views.rejected),
        url(r'^rejected_thread$', views.rejected_thread),

        url(r'^moderate_user_for_thread_get', views.moderate_user_for_thread_get),
    ]

    urlpatterns.extend(new_patterns)
