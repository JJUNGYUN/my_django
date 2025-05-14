from django.urls import path

from . import views

app_name = 'server_dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('gpu_info/', views.gpu_usage, name='gpu_info'),
]