from django.conf.urls import patterns, include, url
from . import views
 
urlpatterns = patterns(
    '',
    url(r'^$', views.index, name='index'),
    url(r'authorize', views.auth, name='return'),
    url(r'callback', views.auth_return, name='return'),
    url(r'import', views.import_start, name='return'),
    url(r'done', views.index, name='return'),
    url(r'forget', views.deauth, name='return'),
)