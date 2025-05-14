from django.urls import path

from . import views

app_name = 'datasets'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:dataset_id>/', views.detail, name='detail'),
    path('new_dataset/', views.new_dataset, name='new_dataset'),
    path('dataset/modify/<int:dataset_id>', views.dataset_modify, name='dataset_modify'),
    path('dataset/delete/<int:dataset_id>', views.dataset_delete, name='dataset_delete'),
    path('dataset/data_studio/<int:dataset_id>/', views.data_studio, name='data_studio'),
    path('<int:dataset_id>/update_readme/', views.update_readme, name='readme_update'),
]