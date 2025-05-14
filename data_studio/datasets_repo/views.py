
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
from django import template
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.urls import reverse

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
        "filter": request.GET.get("filter", "all"),
        "q": request.GET.get("q", ""),
        "reset_url": reverse('datasets:index'),
        "filter_options": {
            "all": "전체",
            "title": "제목",
            "owner": "작성자",
        }
    }

    return render(request, 'datasets/dataset_list.html', context)

def detail(request, dataset_id):
    dataset = get_object_or_404(Datasets, pk=dataset_id)
    dataset_path = dataset.dataset_path
    path = dataset_path
    file_content = None
    target_path= None

    if os.path.isfile(os.path.join(dataset_path,"README.md")):
        with open(os.path.join(dataset_path,"README.md")) as f:
            readme = ''.join(f.readlines())
    else:
        readme = 'README.md가 없어요'

    if request.method == 'POST':
        
        current_path = request.POST.get('current_path')
        target_path = request.POST.get('file_path')
        if target_path=='before':
            path = os.path.dirname(os.path.normpath(current_path))
            print(path)
        else:
            path = os.path.join(current_path,target_path)

        if os.path.isdir(path):
            file_list = get_file_info_from_dir(path)
        else:
            path = current_path
            
            file_list = get_file_info_from_dir(current_path)
            for item in file_list:
                if (item['name'] == target_path) and (float(item['size'].split()[0])<5):
                    try:
                        with open(os.path.join(current_path,target_path)) as f:
                            file_content = '<br>'.join(f.readlines())
                    except Exception as e:
                        file_content = e
                elif (item['name'] == target_path) and (float(item['size'].split()[0])>5):
                    file_content = "파일은 최대 5MiB까지만 확인 가능합니다!"
    elif dataset.dataset_path and os.path.isdir(dataset.dataset_path):
        file_list = get_file_info_from_dir(path)
        
    else:
        file_list = {}


    sample_data =  get_sample_dataset(dataset_path=dataset_path)     
                                      
    context = {'dataset':dataset, 'readme': readme, 'file_list':file_list,'sample_data':sample_data, 'path':path, 'file_content':file_content, "target_path":target_path}


    return render(request, 'datasets/dataset_detail.html',context)

@csrf_exempt
@login_required
def update_readme(request, dataset_id):
    if request.method == 'POST':
        try:
            dataset = Datasets.objects.get(id=dataset_id)

            # 작성자 확인
            # if request.user != dataset.author:
            #     return JsonResponse({'success': False, 'error': '권한이 없습니다.'}, status=403)

            readme_path = os.path.join(dataset.dataset_path, 'README.md')
            readme_content = request.POST.get('readme_content', '')

            # 파일 저장
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)

            # 마크다운 렌더링된 HTML 반환
            rendered_html = readme_content

            return JsonResponse({'success': True, 'updated_html': rendered_html})

        except Datasets.DoesNotExist:
            return JsonResponse({'success': False, 'error': '데이터셋이 존재하지 않습니다.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'}, status=400)


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
        elif 'file_path' in request.POST:
            current_path = request.POST.get('current_path')
            target_path = request.POST.get('file_path')
            if target_path=='before':
                path = os.path.dirname(os.path.normpath(current_path))
                print(path)
            else:
                path = os.path.join(current_path,target_path)

            if os.path.isdir(path):
                file_list = get_file_info_from_dir(path)
            else:
                path = current_path
                file_list = get_file_info_from_dir(current_path)
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
        path = '/root/workspace/'
        if os.path.isdir(path):
            file_list = get_file_info_from_dir(path)
        form = Datasets()
    
    context = {'form':form, 'file_list':file_list, 'path':path}
    return render(request, 'datasets/new_dataset.html', context)

@login_required(login_url='common:login')
def dataset_modify(request, dataset_id):
    dataset = get_object_or_404(Datasets, pk=dataset_id)
    path = dataset.dataset_path

    if request.user != dataset.author:
        messages.error(request, '수정 권한 없음')
        return redirect('datasets:detail',dataset_id=dataset.id)
    if request.method == 'POST':
        form = datasetlForm(request.POST, instance=dataset)
        if 'preview' in request.POST:
            dataset_path = request.POST.get('dataset_path')
            if dataset_path and os.path.isdir(dataset_path):
                file_list = get_file_info_from_dir(dataset_path)
            else:
                file_list = ['dataset_path must be directory path']
        elif 'file_path' in request.POST:
            current_path = request.POST.get('current_path')
            target_path = request.POST.get('file_path')
            if target_path=='before':
                path = os.path.dirname(os.path.normpath(current_path))
                print(path)
            else:
                path = os.path.join(current_path,target_path)

            if os.path.isdir(path):
                file_list = get_file_info_from_dir(path)
            else:
                path = current_path
                file_list = get_file_info_from_dir(current_path)
        elif 'save'  in request.POST:
            if form.is_valid():
            # if 'save' in request.POST:
                dataset = form.save(commit=False)
                dataset.create_date = timezone.now()
                dataset.author = request.user
                dataset.file_size = "TEST"
                dataset.save()
                return redirect('datasets:detail',dataset_id=dataset.id)
    else:
        if os.path.isdir(path):
            file_list = get_file_info_from_dir(path)
        else:
            file_list = []
        form = datasetlForm(instance=dataset)

    context = {'form':form, 'file_list':file_list, 'path':path}
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