from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import HttpResponseNotAllowed
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.urls import reverse
    
from datasets_repo.models import Datasets
from .form import dashboardForm, evalresultForm
from .utils import get_readme
from models.models import LM_models
from .models import Benchmark, BenchmarkResult
from collections import defaultdict
import json



def index(request):
    page = request.GET.get('page','1')  
    q = request.GET.get('q', '')  # 검색어 가져오기

    benchmark_list = Benchmark.objects.order_by('-id')
    if q:
       benchmark_list = benchmark_list.filter(benchmark_name__icontains=q)
    print(q)
    print(benchmark_list)
    paginator = Paginator(benchmark_list, 20)
    page_obj = paginator.get_page(page)

    context = {
        'benchmark_list': page_obj,
        "q": request.GET.get("q", ""),
        "reset_url": reverse('datasets:index'),
        "filter_options": {
            "all": "전체",
            "title": "제목",
            "owner": "작성자",
        }
    }

    return render(request, 'model_dashboard/dashboard_list.html', context)

def get_dashboard(request, benchmark_id):

    benchmark = get_object_or_404(Benchmark, pk=benchmark_id)
    dataset_obj = benchmark.dataset_name

    readme = get_readme(dataset_obj)

    metrics = defaultdict(list)
    benchmark_results = BenchmarkResult.objects.filter(benchmark_name_id=benchmark_id)

    for res in benchmark_results:
        model_name = res.llm_model.name
        metric_res = res.metrics
        metrics['model_name'].append(model_name)
        metrics['model_id'].append(res.llm_model.id)
        for key in benchmark.metrics:
            if key not in metric_res:
                metrics[key].append("N/A")
            else:
                metrics[key].append(metric_res[key])

    header = benchmark.metrics#.keys()
     
    metrics = [dict(zip(metrics.keys(), values)) for values in zip(*metrics.values())]

    context = {'benchmark':benchmark, 'readme': readme,'dataset':dataset_obj, 'rows':metrics,'headers':header,'active_tab': 'readme'}

    return render(request, 'model_dashboard/dashboard.html', context)

def get_eval_result(request, benchmark_id, llm_model_id):
    # Jsonl이나 Json일때 처리 필요하네
    model_obj = get_object_or_404(LM_models, pk=llm_model_id)
    benchmark_pbj = get_object_or_404(Benchmark, pk=benchmark_id)
    dataset_obj = BenchmarkResult.objects.get(benchmark_name=benchmark_pbj, llm_model=model_obj)
    dataset = json.loads(dataset_obj.evaluate_result)
    if isinstance(dataset, list):
        
        dataset = {i:d for i, d in enumerate(dataset)}
    context ={'sample_data': dataset}
    return render(request, 'model_dashboard/eval_result.html', context=context)


@login_required(login_url='common:login')
def create_dashboard(request):
    if request.method == 'POST':
        form = dashboardForm(request.POST)
        dataset_name_str = request.POST.get('dataset_name')
        metrics = set(request.POST.getlist('metrics[]')) or {'N/A'}

        try:
            dataset_obj = Datasets.objects.get(name=dataset_name_str)
        except Datasets.DoesNotExist:
            form.add_error('dataset_name', '입력한 데이터셋이 존재하지 않습니다.')
            dataset_obj = None  # None 설정해서 후속 처리 가능하게
        
        if form.is_valid():
            
            dashboard = form.save(commit=False)
            dashboard.dataset_name = dataset_obj
            dashboard.metrics = list(metrics)
            dashboard.author = request.user
            dashboard.dataset_version = timezone.now()
            dashboard.save()
            return redirect('model_dashboard:index')
        else:
            print("Form errors:", form.errors)
            
    else:
        form = dashboardForm()

    context = {'form':form}

    return render(request, 'model_dashboard/new_dashboard.html',context=context)

@login_required(login_url='common:login')
def delete_dashboard(request, benchmark_id):
    benchmark = get_object_or_404(Benchmark, pk=benchmark_id)
    if request.user != benchmark.author:
        messages.error(request, '삭제 권한 없음')
        return redirect('benchmark:dashboard',benchmark_id=Benchmark.id)
    benchmark.delete()
    return redirect('model_dashboard:index')

import json

def add_eval_result(request, benchmark_id):
    if request.method == 'POST':
        form = evalresultForm(request.POST)
        model_name_str = request.POST.get('model_name')
        benchmark_name_str = request.POST.get('benchmark_name')

        if model_name_str != '':
            try:
                model_obj = LM_models.objects.get(name=model_name_str)
            except LM_models.DoesNotExist:
                form.add_error('model_name', '입력한 모델셋이 존재하지 않습니다.')
                model_obj = None
        
        try:
            benchmark_obj = Benchmark.objects.get(benchmark_name=benchmark_name_str)
        except Benchmark.DoesNotExist:
            form.add_error('benchmark_name', '입력한 벤치마크가 존재하지 않습니다.')
            benchmark_obj = None

        # ✅ 파일 업로드 검사 및 파싱
        uploaded_file = request.FILES.get('json_file')
        evaluate_result = request.POST.get('evaluate_result')

        if uploaded_file:
            try:
                content = uploaded_file.read().decode('utf-8')
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    # JSONL 형식 시도
                    data = [json.loads(line) for line in content.splitlines() if line.strip()]

                # ✅ 구조검사 (모든 아이템이 단일 키-값 쌍인지 확인)
                if isinstance(data, dict):
                    invalids = [v for v in data.values() if isinstance(v, dict)]
                elif isinstance(data, list):
                    invalids = [item for item in data if not isinstance(item, dict) or any(isinstance(v, dict) for v in item.values())]
                else:
                    invalids = ['invalid']

                if invalids:
                    form.add_error('evaluate_result', '모든 데이터는 1단계 딕셔너리 형태여야 합니다. 예: {"1":{"입력": "1+1=", "출력": "2"}} or [{"입력": "1+1=", "출력": "2"}]')
                else:
                    evaluate_result = json.dumps(data, ensure_ascii=False)

            except Exception as e:
                form.add_error('evaluate_result', f'파일 처리 중 오류 발생: {e}')
        
        if form.is_valid() and model_obj and benchmark_obj:
            BenchmarkResult.objects.filter(llm_model=model_obj, benchmark_name=benchmark_obj).delete()
            eval_result = form.save(commit=False)
            eval_result.llm_model = model_obj
            eval_result.benchmark_name = benchmark_obj
            eval_result.evaluate_result = evaluate_result
            eval_result.metrics = {
                key.replace('_score', ''): value
                for key, value in request.POST.items()
                if key.endswith('_score') and value.strip() != ''
            }
            eval_result.author = request.user
            eval_result.dataset_version = timezone.now()
            eval_result.save()
            return redirect('model_dashboard:detail', benchmark_id=benchmark_id)

        dataset_obj = benchmark_obj.dataset_name if benchmark_obj else None
        readme = get_readme(dataset_obj) if dataset_obj else ""
        scores = {
            key.replace('_score', ''): value
            for key, value in request.POST.items()
            if key.endswith('_score') and value.strip() != ''
        }

        return render(request, 'model_dashboard/dashboard.html', {
            'form': form,
            'readme': readme,
            'benchmark': benchmark_obj,
            'headers': benchmark_obj.metrics if benchmark_obj else [],
            'evaluate_result': evaluate_result,
            'scores': scores,
            'active_tab': 'add_eval_result',
        })



@require_GET
def dataset_autocomplete(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.GET.get('term', '')
        results = Datasets.objects.filter(name__icontains=query).values_list('name', flat=True)
        return JsonResponse(list(results), safe=False)
    return JsonResponse([], safe=False)

@require_GET
def model_autocomplete(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.GET.get('term', '')
        results = LM_models.objects.filter(name__icontains=query).values_list('name', flat=True)
        return JsonResponse(list(results), safe=False)
    return JsonResponse([], safe=False)