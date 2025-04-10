from django.urls import path

from . import views

app_name = 'model_dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:benchmark_id>/', views.get_dashboard, name='detail'), #'<int:dataset_id>/'
    path('new_dashboard/', views.create_dashboard, name='new_dashboard'),
    path('model_dashboard/delete/<int:benchmark_id>', views.delete_dashboard, name='delete_dashboard'),
    path('autocomplete/datasets/', views.dataset_autocomplete, name='dataset_autocomplete'),
    path('autocomplete/models/', views.model_autocomplete, name='model_autocomplete'),
    path('add_eval_result/<int:benchmark_id>', views.add_eval_result, name='add_eval_result'),
    path('<int:benchmark_id>/<int:llm_model_id>/eval_viewer', views.get_eval_result, name='eval_viewer'),

]