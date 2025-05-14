from .models import LM_models
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
from django import template
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.urls import reverse

from .form import modelForm
from .utils import get_file_info_from_dir

import os

register = template.Library()

def index(request):
    page = request.GET.get('page', '1')  
    q = request.GET.get('q', '')  # 검색어
    filter_type = request.GET.get('filter', 'all')
    tag_filter = request.GET.get('tag', '')  # Two level nav에서 들어온 값

    model_list = LM_models.objects.order_by('-id')

    # 태그 필터 우선 적용
    if tag_filter:
        model_list = model_list.filter(
            Q(tag__icontains=tag_filter) | Q(task_type__icontains=tag_filter)
        )

    # 일반 검색 필터 적용
    if q:
        if filter_type == 'title':
            model_list = model_list.filter(name__icontains=q)
        elif filter_type == 'tag':
            model_list = model_list.filter(
                Q(tag__icontains=q) | Q(task_type__icontains=q)
            )
        elif filter_type == 'author':
            try:
                user = User.objects.get(username=q)
                model_list = model_list.filter(author=user)
            except User.DoesNotExist:
                model_list = LM_models.objects.none()
        else:
            model_list = model_list.filter(
                Q(name__icontains=q) |
                Q(tag__icontains=q) |
                Q(author__username__icontains=q) | 
                Q(task_type__icontains=q)
            )

    paginator = Paginator(model_list, 15)
    page_obj = paginator.get_page(page)

    context = {
        'models_list': page_obj,
        'filter': filter_type,
        'tag_filter': tag_filter,  # 필요시 템플릿에서 사용
        "q": request.GET.get("q", ""),
        "reset_url": reverse('datasets:index'),
        "filter_options": {
            "all": "전체",
            "title": "제목",
            "owner": "작성자",
        }
    }

    return render(request, 'models/model_list.html', context)


def detail(request, model_id):
    # 1) 기본 모델 & 경로 설정
    model = get_object_or_404(LM_models, pk=model_id)
    base_path = model.weight_path

    # 2) README.md 로드 (or 초기 메시지)
    readme_path = os.path.join(base_path, "README.md")
    if os.path.isdir(base_path):
        if os.path.isfile(readme_path):
            with open(readme_path, encoding="utf-8") as f:
                readme = f.read()
        else:
            readme = "README.md가 없어요"
    else:
        readme = "이런! 누가 데이터를 지웠나봐요!"

    # 3) 브라우저에서 현재 탐색 중인 경로와 선택된 항목
    #    POST 로 “file_path” 가 넘어오면, 탐색 동작
    current_path = request.POST.get("current_path", base_path)
    target_path  = request.POST.get("file_path", None)
    file_content = None

    # 4) README 수정 처리
    if request.method == "POST" and "readme" in request.POST:
        if request.user == model.author:
            new_text = request.POST["readme"]
            try:
                with open(readme_path, "w", encoding="utf-8") as f:
                    f.write(new_text)
                readme = new_text
                messages.success(request, "README가 성공적으로 저장되었습니다.")
            except Exception as e:
                messages.error(request, f"README 저장 실패: {e}")
        return redirect(request.path)  # 새로고침

    # 5) 파일/폴더 탐색 처리
    if request.method == "POST" and target_path:
        # “..” 클릭 시 부모 폴더
        if target_path == "before":
            new_path = os.path.dirname(os.path.normpath(current_path))
        else:
            new_path = os.path.normpath(os.path.join(current_path, target_path))

        # 실제로 파일 시스템 상에 존재하는지 먼저 확인
        if os.path.isdir(new_path):
            # └ 디렉토리: 해당 폴더 목록만 로드
            current_path = new_path
            file_content = None
            file_list = get_file_info_from_dir(current_path)

        elif os.path.isfile(new_path):
            # └ 파일: 동일 폴더 목록 + 내용만 읽기
            current_path = os.path.dirname(new_path)
            file_list = get_file_info_from_dir(current_path)

            # 5MiB 이하만 읽고, 나머지는 경고 메시지
            try:
                size_mb = os.path.getsize(new_path) / (1024 * 1024)
                if size_mb <= 5:
                    with open(new_path, encoding="utf-8") as f:
                        file_content = "<br>".join(f.readlines())
                else:
                    file_content = "파일은 최대 5MiB까지만 확인 가능합니다!"
            except Exception:
                file_content = "파일을 읽는 중 오류가 발생했습니다."

        else:
            # └ 그 외(존재하지 않거나 권한 문제): 기본 폴더 목록 복원
            current_path = base_path
            file_content = None
            file_list = get_file_info_from_dir(base_path)

    else:
        # 최초 로드 또는 GET: 기본 폴더 목록
        current_path = base_path
        file_content = None
        file_list = get_file_info_from_dir(base_path)


    # 6) 컨텍스트 전달
    return render(request, "models/model_detail.html", {
        "model": model,
        "readme": readme,
        "file_list": file_list,
        "path": current_path,
        "file_content": file_content,
        "target_path": target_path,
    })


@csrf_exempt
def save_readme(request, model_id):
    if request.method == 'POST':
        model = get_object_or_404(LM_models, pk=model_id)
        if request.user != model.author:
            return JsonResponse({"success": False, "error": "권한 없음"}, status=403)

        try:
            data = json.loads(request.body)
            readme_text = data.get("readme", "")
            readme_path = os.path.join(model.weight_path, "README.md")
            with open(readme_path, "w", encoding='utf-8') as f:
                f.write(readme_text)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


@login_required(login_url='common:login')
def new_model(request):
    print(request.method)
    file_list = []
    path = '/root/workspace/'

    if request.method == 'POST':
        form = modelForm(request.POST)

        # 디렉터리 미리보기
        if 'preview' in request.POST:
            weight_path = request.POST.get('weight_path')
            if weight_path and os.path.isdir(weight_path):
                file_list = get_file_info_from_dir(weight_path)
            else:
                file_list = ['weight_path must be directory path']

        # 파일 탐색
        elif 'file_path' in request.POST:
            current_path = request.POST.get('current_path')
            target_path = request.POST.get('file_path')
            if target_path == 'before':
                path = os.path.dirname(os.path.normpath(current_path))
            else:
                path = os.path.join(current_path, target_path)

            if os.path.isdir(path):
                file_list = get_file_info_from_dir(path)
            else:
                # 경로가 유효하지 않으면 이전 경로 유지
                path = current_path
                file_list = get_file_info_from_dir(current_path)

        # 저장 처리
        elif 'save' in request.POST:
            if form.is_valid():
                model = form.save(commit=False)
                model.create_date = timezone.now()
                model.author = request.user
                # 태그 처리: 쉼표로 분리, 공백 제거 후 다시 쉼표 결합
                raw_tags = json.loads(request.POST.get('tag', ''))
                cleaned_tags = [t['value'] for t in raw_tags]
                model.tag = ','.join(cleaned_tags)
                # task_type 은 폼에서 바로 가져오도록 수정했으면 아래 라인 제거 가능
                model.task_type = request.POST.get('task_type')
                # 파일 사이즈 자동 적용 원하면 os.path.getsize() 사용
                model.file_size = "110MB"
                model.save()
                return redirect('models:index')

    else:
        # GET 요청: 기본 경로로 초기 파일 목록 로드
        if os.path.isdir(path):
            file_list = get_file_info_from_dir(path)
        form = modelForm()

    context = {
        'form': form,
        'file_list': file_list,
        'path': path,
    }
    return render(request, 'models/new_model.html', context)

@login_required(login_url='common:login')
def model_modify(request, model_id):
    model = get_object_or_404(LM_models, pk=model_id)
    if request.user != model.author:
        messages.error(request, '수정 권한 없음')
        return redirect('models:detail',model_id=model.id)
    if request.method == 'POST':
        form = modelForm(request.POST, instance=model)
        if form.is_valid():
            model = form.save(commit=False)
            model.create_date = timezone.now()
            model.author = request.user
            model.save()
            return redirect('models:detail',model_id=model.id)
    else:
        form = modelForm(instance=model)

    context = {'form':form}
    return render(request, 'models/new_model.html', context)

@login_required(login_url='common:login')
def model_delete(request, model_id):
    model = get_object_or_404(LM_models, pk=model_id)
    if request.user != model.author:
        messages.error(request, '삭제 권한 없음')
        return redirect('models:detail',model_id=model.id)
    model.delete()
    return redirect('models:index')