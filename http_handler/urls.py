from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
     url(r'^$', 'http_handler.views.index'),
	 (r'^account/', include('account.urls')),
	 (r'^browser/', include('browser.urls')),
)