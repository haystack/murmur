from django.conf.urls import patterns, include, url
from . import views
 
urlpatterns = patterns(
    '',
    url(r'^$', views.index, name='index'),
    url(r'authorize', views.auth, name='auth'),
    url(r'callback', views.auth_return, name='return'),
    url(r'import', views.import_start, name='import'),
    url(r'done', views.index, name='done'),
    url(r'forget', views.deauth, name='forget'),
)