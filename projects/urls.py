from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='projects-index'),
    url(r'^create/$', views.create, name='projects-create'),
    url(r'^view/(?P<project_id>[0-9]+)/$', views.view, name='projects-view'),
    url(r'^update/(?P<pk>[0-9]+)/$', views.ProjectUpdate.as_view(), name='projects-update'),
    url(r'^delete/(?P<pk>[0-9]+)/$', views.ProjectDelete.as_view(), name='projects-delete'),
    url(r'^import_files/(?P<project_id>[0-9]+)/$', views.import_files, name='projects-import-files'),
    url(r'^import_project_files/(?P<project_id>[0-9]+)/$', views.import_project_files, name='import_project_files')  
]
