from django.contrib.auth import logout, authenticate, login
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .forms import UserForm

from common.forms import UserForm
from playground.models import Playground
from models.models import LM_models
from label_studio.models import Project
from datasets_repo.models import Datasets
from .forms import ProfileForm

# Create your views here.
def logout_view(request):
    logout(request)
    return redirect('index')

def signup(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            user_id = form.cleaned_data.get('id')
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=user_id, password=raw_password)
            # form.save()
            if user is not None:
                login(request, user)
            return redirect('index')
    else:
        form = UserForm()
    
    return render(request, 'common/signup.html',{'form':form})

@login_required(login_url='common:login')
def mypage(request):
    user = request.user

    playground_list = Playground.objects.filter(author=user) \
                                        .order_by('-start_time')

    llm_models_list = LM_models.objects.filter(author=user) \
                                        .order_by('-create_date')

    project_list = Project.objects.filter(
        Q(owner=user) |
        Q(assignments__worker=user)
    ).distinct().order_by('-created_at')

    datasets_list = Datasets.objects.filter(author=user) \
                                     .order_by('-create_date')

    return render(request, 'common/mypage.html', {
        'playground_list': playground_list,
        'models_list':    llm_models_list,
        'project_list':   project_list,
        'datasets_list':  datasets_list,
    })



@login_required(login_url='common:login')
def profile_edit_view(request):
    """
    회원이 자신의 한글 이름(first_name), 영문 이름(last_name),
    비밀번호(password1/password2)를 수정하는 뷰입니다.
    ID(username)는 readonly로 표시만 합니다.
    """
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            # 비밀번호 변경 처리
            pw = form.cleaned_data.get('password1')
            if pw:
                user.set_password(pw)
            # 한글/영문 이름은 폼이 자동 반영
            user.save()

            # 비밀번호 변경 시, 세션 유지
            if pw:
                update_session_auth_hash(request, user)

            messages.success(request, "프로필이 성공적으로 수정되었습니다.")
            return redirect('common:profile_edit')
        else:
            messages.error(request, "입력값을 다시 확인해주세요.")
    else:
        form = ProfileForm(instance=request.user)
        # 비밀번호 필드 autocomplete 방지
        form.fields['password1'].widget.attrs.update({'autocomplete': 'new-password'})
        form.fields['password2'].widget.attrs.update({'autocomplete': 'new-password'})

    return render(request, 'common/profile_edit.html', {
        'form': form,
    })