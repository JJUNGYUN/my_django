from django.urls import path
from . import views

app_name = 'playground'

urlpatterns = [
    path('', views.index, name='index'),
    path('new_playground/', views.new_playground, name='new_playground'),
    path('<int:pk>/', views.detail, name='detail'),  # 수정된 라인
    path('delete/<int:pk>/', views.delete_playground, name='delete'),  # 수정된 라인
    path('autocomplete/models/', views.model_autocomplete, name='model_autocomplete'),
]
