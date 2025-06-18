from django.urls import path
from . import views

app_name = 'channels'

urlpatterns = [
    path('', views.channel_list_view, name='list'),
    path('connect/', views.connect_channel_view, name='connect'),
    path('shopify/connect/', views.shopify_connect_view, name='shopify_connect'),
    path('shopify/callback/', views.shopify_callback_view, name='shopify_callback'),
    path('<uuid:channel_id>/test/', views.test_channel_connection, name='test_connection'),
    path('<uuid:channel_id>/disconnect/', views.disconnect_channel, name='disconnect'),
]