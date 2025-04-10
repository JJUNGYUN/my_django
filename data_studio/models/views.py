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

from .form import modelForm
from .utils import get_file_info_from_dir

import os

register = template.Library()


# Create your views here.
def index(request):
    page = request.GET.get('page', '1')  
    q = request.GET.get('q', '')  # 검색어 가져오기
    filter_type = request.GET.get('filter','all')

    # 이름 기준 필터링
    model_list = LM_models.objects.order_by('-id')
    if q:
        if filter_type == 'title':
            model_list = model_list.filter(name__icontains=q)
        elif filter_type == 'tag':
            model_list = model_list.filter(tag__icontains=q)
        elif filter_type == 'author':
            try:
                user = User.objects.get(username=q)
                
                model_list = model_list.filter(author__username__icontains=user)
            except User.DoesNotExist:
                model_list = []
        else:
            # 전체에서 검색 (제목 + 태그 + 작성자)
            model_list = model_list.filter(
                Q(name__icontains=q) |
                Q(tag__icontains=q) |
                Q(author__username__icontains=q)
            )

    paginator = Paginator(model_list, 20)
    page_obj = paginator.get_page(page)

    context = {
        'models_list': page_obj,
        'q': q,  # 템플릿에서 value 유지용
    }

    return render(request, 'models/model_list.html', context)

def detail(request, model_id):
    model = get_object_or_404(LM_models, pk=model_id)
    model_path = model.weight_path

    if os.path.isdir(model_path):
        if os.path.isfile(os.path.join(model_path,"README.md")):
            with open(os.path.join(model_path,"README.md")) as f:
                readme = ''.join(f.readlines())
        else:
            readme = 'README.md가 없어요'
    else:
        readme = "이런! 누가 데이터를 지웠나봐요!"

    if model.weight_path and os.path.isdir(model.weight_path):
        file_list = get_file_info_from_dir(model.weight_path)
    else:
        file_list = {}
                                                   
    context = {'model':model, 'readme': readme, 'file_list':file_list}


    return render(request, 'models/model_detail.html',context)

@login_required(login_url='common:login')
def new_model(request):
    file_list = []
    if request.method == 'POST':
        form = modelForm(request.POST)
        if 'preview' in request.POST:
                weight_path = request.POST.get('weight_path')
                if weight_path and os.path.isdir(weight_path):
                    file_list = get_file_info_from_dir(weight_path)
                else:
                    file_list = ['weight_path must be directory path']
        elif 'save' in request.POST:
            if form.is_valid():
                model = form.save(commit=False)
                model.create_date = timezone.now()
                model.author = request.user
                model.file_size = "110MB"
                model.save()
                return redirect('models:index')
            
    else:
        form = LM_models()

    context = {'form':form, 'file_list':file_list}
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