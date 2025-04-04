from django.urls import path

from . import views

app_name = 'models'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:question_id>/', views.detail, name='detail'),
    path('new_model/', views.new_model, name='new_model'),
]