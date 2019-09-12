from django.conf.urls import patterns, include, url
from django.contrib import admin
from onadata.apps.reports import views,views_report

urlpatterns = patterns('',
    #url(r'^profile_view/(?P<victim_id>\d+)/$', views.profile_view,name='profile_view'),
    url(r'^post-arrival-immediate-assistance/$', views.post_arrival_immediate_assistance,name='post_arrival_immediate_assistance'),
    url(r'^get_post_arrival_immediate_assistance/$', views.get_post_arrival_immediate_assistance,name='get_post_arrival_immediate_assistance'),
    url(r'^generate_report/(?P<sub_module>[^/]+)/$', views_report.report_initial),
    url(r'^get_report_elements/(?P<sub_module>[^/]+)/$', views_report.generate_report),
    url(r'^generate_filter/$', views_report.get_filters),
    url(r'^get_sustainability_report/$', views_report.sustainability_report,
                           name='sustainability_report'),



    )
