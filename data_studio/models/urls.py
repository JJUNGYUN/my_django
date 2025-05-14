from django.urls import path

from . import views

app_name = 'models'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:model_id>/', views.detail, name='detail'),
    path('new_model/', views.new_model, name='new_model'),
    path('models/modify/<int:model_id>', views.model_modify, name='model_modify'),
    path('models/delete/<int:model_id>', views.model_delete, name='model_delete'),
    path('<int:model_id>/save_readme/', views.save_readme, name='save_readme'),

]