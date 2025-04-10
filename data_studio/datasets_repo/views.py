
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
from django import template
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User

from .models import Datasets
from .form import datasetlForm
from .utils import get_file_info_from_dir, get_sample_dataset

import os

register = template.Library()


# Create your views here.
def index(request):
    page = request.GET.get('page', '1')  
    q = request.GET.get('q', '')  # 검색어 가져오기
    filter_type = request.GET.get('filter','all')

    # 이름 기준 필터링
    datasets_list = Datasets.objects.order_by('-id')
    if q:
        if filter_type == 'title':
            datasets_list = datasets_list.filter(name__icontains=q)
        elif filter_type == 'tag':
            datasets_list = datasets_list.filter(tag__icontains=q)
        elif filter_type == 'author':
            try:
                user = User.objects.get(username=q)
                
                datasets_list = datasets_list.filter(author__username__icontains=user)
            except User.DoesNotExist:
                datasets_list = []
        else:
            # 전체에서 검색 (제목 + 태그 + 작성자)
            datasets_list = datasets_list.filter(
                Q(name__icontains=q) |
                Q(tag__icontains=q) |
                Q(author__username__icontains=q)
            )

    paginator = Paginator(datasets_list, 20)
    page_obj = paginator.get_page(page)

    context = {
        'datasets_list': page_obj,
        'q': q,  # 템플릿에서 value 유지용
    }

    return render(request, 'datasets/dataset_list.html', context)

def detail(request, dataset_id):
    dataset = get_object_or_404(Datasets, pk=dataset_id)
    dataset_path = dataset.dataset_path

    if os.path.isfile(os.path.join(dataset_path,"README.md")):
        with open(os.path.join(dataset_path,"README.md")) as f:
            readme = ''.join(f.readlines())
    else:
        readme = 'README.md가 없어요'

    if dataset.dataset_path and os.path.isdir(dataset.dataset_path):
        file_list = get_file_info_from_dir(dataset.dataset_path)

                                          
    
    sample_data =  get_sample_dataset(dataset_path=dataset_path)     
                                      
    context = {'dataset':dataset, 'readme': readme, 'file_list':file_list,'sample_data':sample_data}


    return render(request, 'datasets/dataset_detail.html',context)

@login_required(login_url='common:login')
def new_dataset(request):
    file_list = []
    if request.method == 'POST':
        form = datasetlForm(request.POST)

        if 'preview' in request.POST:
            dataset_path = request.POST.get('dataset_path')
            if dataset_path and os.path.isdir(dataset_path):
                file_list = get_file_info_from_dir(dataset_path)
            else:
                file_list = ['dataset_path must be directory path']
        elif 'save'  in request.POST:
            if form.is_valid():
            # if 'save' in request.POST:
                dataset = form.save(commit=False)
                dataset.create_date = timezone.now()
                dataset.author = request.user
                dataset.file_size = "TEST"
                dataset.save()
                return redirect('datasets:index')
            
    else:
        form = Datasets()

    context = {'form':form, 'file_list':file_list}
    return render(request, 'datasets/new_dataset.html', context)


@login_required(login_url='common:login')
def dataset_modify(request, dataset_id):
    dataset = get_object_or_404(Datasets, pk=dataset_id)
    if request.user != dataset.author:
        messages.error(request, '수정 권한 없음')
        return redirect('datasets:detail',dataset_id=dataset.id)
    if request.method == 'POST':
        form = datasetlForm(request.POST, instance=dataset)
        if form.is_valid():
            dataset = form.save(commit=False)
            dataset.create_date = timezone.now()
            dataset.author = request.user
            dataset.save()
            return redirect('datasets:detail',dataset_id=dataset.id)
    else:
        form = datasetlForm(instance=dataset)

    context = {'form':form}
    return render(request, 'datasets/new_dataset.html', context)

@login_required(login_url='common:login')
def dataset_delete(request, dataset_id):
    dataset = get_object_or_404(Datasets, pk=dataset_id)
    if request.user != dataset.author:
        messages.error(request, '삭제 권한 없음')
        return redirect('datasets:detail',dataset_id=dataset.id)
    dataset.delete()
    return redirect('datasets:index')

def data_studio(request, dataset_id):
    dataset = get_object_or_404(Datasets, pk=dataset_id)
    dataset_path = dataset.dataset_path

    if os.path.isfile(os.path.join(dataset_path,"README.md")):
        with open(os.path.join(dataset_path,"README.md")) as f:
            readme = ''.join(f.readlines())
    else:
        readme = 'README.md가 없어요'

    if dataset.dataset_path and os.path.isdir(dataset.dataset_path):
        file_list = get_file_info_from_dir(dataset.dataset_path)

    sample_data =  get_sample_dataset(dataset_path=dataset_path)     

    context = {'dataset':dataset, 'readme': readme, 'file_list':file_list,'sample_data':sample_data}


    return render(request, 'datasets/dataset_studio.html',context)