"""
URL patterns for the views included in ``django.contrib.auth``.

Including these URLs (via the ``include()`` directive) will set up the
following patterns based at whatever URL prefix they are included
under:

* User login at ``login/``.

* User logout at ``logout/``.

* The two-step password change at ``password_change/`` and
  ``password_change/done/``.

* The four-step password reset at ``password_reset/``,
  ``reset/``, ``reset/done`` and
  ``password_reset_done/``.

The default registration backend already has an ``include()`` for
these URLs, so under the default setup it is not necessary to manually
include these views. Other backends may or may not include them;
consult a specific backend's documentation for details.

"""

from django.conf.urls import url
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

from http_handler.settings import WEBSITE

website_context = {'website' : WEBSITE}

urlpatterns = [
    url(r'^login/$', LoginView.as_view(template_name='registration/login.html', 
            extra_context=website_context), 
            name='auth_login'),
    url(r'^logout/$', LogoutView.as_view(template_name='registration/logout.html', 
            extra_context=website_context, next_page=reverse_lazy('login')), 
            name='auth_logout'),
    url(r'^password_change/$', PasswordChangeView.as_view(), name='auth_password_change'),
    url(r'^password_change/done/$', PasswordChangeDoneView.as_view(), name='auth_password_change_done'),
    url(r'^password_reset/$', PasswordResetView.as_view(), name='auth_password_reset'),
    url(r'^password_reset/done/$', PasswordResetDoneView.as_view(), name='auth_password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', PasswordResetConfirmView.as_view(), name='auth_password_reset_confirm'),
    url(r'^rest/done/$', PasswordResetCompleteView.as_view(), name='auth_password_reset_complete'),
]