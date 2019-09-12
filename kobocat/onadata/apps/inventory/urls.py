from django.conf.urls import patterns, include, url
from django.contrib import admin
from onadata.apps.inventory import views

urlpatterns = patterns('',
    #url(r'^profile_view/(?P<victim_id>\d+)/$', views.profile_view,name='profile_view'),
    url(r'^$', views.index,name='index'),
    url(r'^get_product_table/$', views.get_product_table,name='get_product_table'),
    url(r'^add_product/$', views.add_product,name='add_product'),
    url(r'^stockin_product/$', views.stockin_product,name='stockin_product'),
    url(r'^check_stockout_qty/$', views.check_stockout_qty,name='check_stockout_qty'),
    url(r'^stockout_product/$', views.stockout_product,name='stockout_product'),
    url(r'^get_stockout_history_data/$', views.get_stockout_history_data,name='get_stockout_history_data'),
url(r'^get_stockin_history_data/$', views.get_stockin_history_data,name='get_stockin_history_data'),





    )
