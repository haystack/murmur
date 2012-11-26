from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
     url(r'^mailx$', 'http_handler.views.index'),
	 url(r'^mailx/index$', 'http_handler.views.index'),
	 (r'^mailx/account/', include('account.urls')),
	 (r'^mailx/browser/', include('browser.urls')),
)