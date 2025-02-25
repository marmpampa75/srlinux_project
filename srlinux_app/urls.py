from django.urls import path
from . import views
from .views import device_list, get_device_uptime

urlpatterns = [
    path('', views.login_view, name='login'),
    path('list/', views.device_list, name='device_list'),
    path('api/uptime/', get_device_uptime, name='get_device_uptime'),
    #path('add/', views.add_device, name='add_device'),
    path('<int:device_id>/interfaces/', views.device_interfaces, name='device_interfaces'),
    path('logout/', views.logout_confirmation, name='logout_confirmation'),
    path('logout/confirmed/', views.logout_confirmed, name='logout_confirmed'),
]