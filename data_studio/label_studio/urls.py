from django.urls import path

from . import views

app_name = "label_studio"

urlpatterns = [
    path("", views.index, name="index"),
    # path("project/", views.project, name="project"),
    path("project/<int:project_id>/upload/", views.upload_input_data_view, name="upload_input_data"),
    path("project/<int:project_id>/add_label/", views.add_label_view, name="add_label"),
    path("project/<int:project_id>/label/<int:label_id>/delete/", views.delete_label_view, name="delete_label"),
    path("project/<int:project_id>/input/<int:input_id>/delete/", views.delete_input_view, name="delete_input"),

    path("project/<int:project_id>/go/", views.project_redirect_view, name="project"),
    path("project/<int:project_id>/detail/", views.project_detail_view, name="project_detail"),
    
    path("project/<int:project_id>/work/", views.work_view, name="work_entry"),
    path("project/<int:project_id>/work/submit/", views.submit_work_view,name="submit_work"),


    path("project/<int:project_id>/download/all/", views.download_all_results, name="download_all"),
    path("project/<int:project_id>/download/user/<int:user_id>/", views.download_user_results, name="download_user"),
    path("project/<int:project_id>/add-workers/", views.add_workers_view, name="add_workers"),
    path("project/<int:project_id>/remove-worker/<int:user_id>/", views.remove_worker_view, name="remove_worker"),
    path("project/<int:project_id>/sync-workers/", views.sync_workers_view, name="sync_workers"),
    path("project/<int:project_id>/modify/", views.modify_project_view, name="modify_project"),
    path("project/<int:project_id>/delete/", views.delete_project, name="delete_project"),
    path("create/", views.project_create_view, name="create"),  # 선택 사항

    path("guideline/<int:project_id>/", views.guideline_view, name="guideline_summary"),
]