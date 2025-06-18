from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('getting-started/', views.getting_started_view, name='getting_started'),
]

# Custom error handlers
handler404 = 'core.views.custom_404'
handler500 = 'core.views.custom_500'