from django.urls import path
from django.contrib.auth import views as auth_views

app_name = 'common'

urlpatterns = [
    # Django에서 지원하는 views 라이브러리를 활용 (로그인, 로그아웃, 비밀번호 찾기 & 초기화 등)
    path('login/', auth_views.LoginView.as_view(template_name = "common/login.html"), name = "login")
]