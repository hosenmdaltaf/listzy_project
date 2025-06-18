from django.urls import path
from . import views, publish

app_name = 'products'

urlpatterns = [
    path('', views.product_list_view, name='list'),
    path('create/', views.product_create_view, name='create'),
    path('<uuid:product_id>/', views.product_detail_view, name='detail'),
    path('<uuid:product_id>/delete/', views.product_delete_view, name='delete'),
    path('<uuid:product_id>/ai-description/', views.generate_ai_description, name='ai_description'),
    
    # Publishing endpoints
    path('<uuid:product_id>/listings/', publish.product_listings_view, name='listings'),
    path('<uuid:product_id>/publish-all/', publish.publish_product_to_all_channels, name='publish_all'),
    path('<uuid:product_id>/publish/<uuid:channel_id>/', publish.publish_product_to_channel, name='publish_to_channel'),
]