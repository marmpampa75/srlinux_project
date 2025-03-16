from django.urls import path
from . import views
from .views import device_list, get_device_uptime, add_device, delete_device, confirm_delete

urlpatterns = [
    path('', views.login_view, name='login'),
    path('list/', views.device_list, name='device_list'),
    path('api/uptime/', get_device_uptime, name='get_device_uptime'),
    path('add-device/', add_device, name='add_device'),
    path('delete-device/', delete_device, name='delete_device'),
    path('device/delete/<int:device_id>/', views.confirm_delete, name='confirm_delete'),
    path('<int:device_id>/interfaces/', views.device_interfaces, name='device_interfaces'),
    path('logout/', views.logout_confirmation, name='logout_confirmation'),
    path('logout/confirmed/', views.logout_confirmed, name='logout_confirmed'),
]