from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from django.db.models import Q, Max
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.dateparse import parse_date
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ProjectCreateForm
from .models import Project, Assignment, WorkResult, InputData, Label

import os
import json

User = get_user_model()

def index(request):
    q = request.GET.get("q", "")
    filter_option = request.GET.get("filter", "all")

    projects = Project.objects.all().select_related("owner")

    if q:
        if filter_option == "title":
            projects = projects.filter(title__icontains=q)
        elif filter_option == "owner":
            projects = projects.filter(owner__username__icontains=q)
        else:
            projects = projects.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(owner__username__icontains=q)
            )

    paginator = Paginator(projects, 8)  # 한 페이지당 8개씩
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "project_list": page_obj,
        "filter": request.GET.get("filter", "all"),
        "q": request.GET.get("q", ""),
        "reset_url": reverse('label_studio:index'),
        "filter_options": {
            "all": "전체",
            "title": "제목",
            "owner": "작성자",
        }
    }
    return render(request, "label_studio/project_list.html", context)

def project_redirect_view(request, project_id):
    if not request.user.is_authenticated:
        # 로그인되지 않은 사용자는 로그인 페이지로 이동
        return redirect_to_login(request.get_full_path(), login_url='/common/login/')

    project = get_object_or_404(Project, id=project_id)

    if request.user == project.owner:
        return redirect("label_studio:project_detail", project_id=project.id)
    elif project.workers.filter(id=request.user.id).exists():
        return redirect("label_studio:work_entry", project_id=project.id)
    else:
        return render(request, "label_studio/no_permission.html", status=403)

@login_required
def project_detail_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    user = request.user
    
    data_order = request.GET.get('data_order')
    if not data_order:

        # 필터링 파라미터
        worker_id = request.GET.get("worker")
        input_id = request.GET.get("input")

        # 기본 queryset
        work_results = WorkResult.objects.filter(project=project).select_related('worker', 'input_data')

        if worker_id:
            work_results = work_results.filter(worker_id=worker_id)
        if input_id:
            work_results = work_results.filter(input_data_id=input_id)

        paginator = Paginator(work_results, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        assignments = Assignment.objects.filter(project=project).select_related('worker')

        input_data_queryset = InputData.objects.filter(project=project).order_by('order')
        input_paginator = Paginator(input_data_queryset, 10)
        input_page_number = request.GET.get("input_page")
        input_page_obj = input_paginator.get_page(input_page_number)


        labels = Label.objects.filter(project=project).order_by('order')
        users = User.objects.all()
        assigned_users = project.workers.all()

        try:
            selected_worker = int(worker_id) if worker_id else None
        except ValueError:
            selected_worker = None

        try:
            selected_input = int(input_id) if input_id else None
        except ValueError:
            selected_input = None

        context = {
            'project': project,
            'assignments': assignments,
            'input_data': input_page_obj,
            'labels': labels,
            'users': users,
            'assigned_users': assigned_users,
            'all_user_work_results': page_obj,
            'selected_worker': selected_worker,
            'selected_input': selected_input,
        }
        context.update(get_work_detail(project, user))

        return render(request, 'label_studio/manager_page.html', context)
           
    
    return move_work_page_view(request, project)


def download_all_results(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    results = WorkResult.objects.filter(project=project).select_related('input_data', 'worker')

    response = HttpResponse(content_type='application/jsonl')
    response['Content-Disposition'] = f'attachment; filename="project_{project_id}_results.jsonl"'

    lines = []
    for r in results:
        record = {
            "input_id": r.input_data.id,
            "order": r.input_data.order,
            "worker": r.worker.username,
            "input_data": r.input_data.data,  # dict
            "result": r.result,               # dict
            "status": r.status,
            "created_at": r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        lines.append(json.dumps(record, ensure_ascii=False))  # 한글 깨짐 방지

    response.write("\n".join(lines))
    return response


def download_user_results(request, project_id, user_id):
    project = get_object_or_404(Project, id=project_id)
    # Resolve the user by username
    user = get_object_or_404(User, id=user_id)

    # Filter by that user's work results
    results = WorkResult.objects.filter(
        project=project,
        worker=user
    ).select_related('input_data', 'worker')

    response = HttpResponse(content_type='application/jsonl')
    response['Content-Disposition'] = (
        f'attachment; filename="project_{project_id}_user_{user.username}_results.jsonl"'
    )

    lines = []
    for r in results:
        record = {
            "input_id": r.input_data.id,
            "order": r.input_data.order,
            "worker": r.worker.username,
            "input_data": r.input_data.data,
            "result": r.result,
            "status": r.status,
            "created_at": r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        lines.append(json.dumps(record, ensure_ascii=False))

    response.write("\n".join(lines))
    return response

@require_POST
def add_workers_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    worker_ids = request.POST.getlist("workers")
    added = 0
    for user_id in worker_ids:
        try:
            user = User.objects.get(id=int(user_id))
            if user.id == project.owner_id:
                continue
            _, created = Assignment.objects.get_or_create(project=project, worker=user)
            if created:
                added += 1
        except (User.DoesNotExist, ValueError):
            continue

    messages.success(request, f"{added}명의 작업자가 프로젝트에 추가되었습니다.")

    
    return redirect("label_studio:project_detail", project_id=project_id)

@require_POST
@login_required
def remove_worker_view(request, project_id, user_id):
    project = get_object_or_404(Project, id=project_id)
    if user_id == project.owner_id:
        return JsonResponse({'error': '오너는 제거할 수 없습니다.'}, status=400)

    deleted, _ = Assignment.objects.filter(project=project, worker_id=user_id).delete()
    if deleted:
        return JsonResponse({'success': True})
    return JsonResponse({'error': '해당 작업자가 존재하지 않습니다.'}, status=404)

@require_POST
@login_required
def modify_project_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    # 권한 체크 (owner만 수정 가능)
    if project.owner != request.user:
        messages.error(request, "수정 권한이 없습니다.")
        return redirect('label_studio:project_detail', project_id=project.id)

    # 값 업데이트
    project.description = request.POST.get("description", "")
    project.start_date = parse_date(request.POST.get("start_date"))
    project.end_date = parse_date(request.POST.get("end_date"))
    project.task_status = request.POST.get("task_status", project.task_status)

    project.save()
    messages.success(request, "프로젝트 정보가 저장되었습니다.")
    return redirect("label_studio:project_detail", project_id=project.id)

@login_required
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    # 소유자만 삭제 가능
    if project.owner != request.user:
        messages.error(request, "프로젝트 삭제 권한이 없습니다.")
        return redirect('label_studio:modify_project', project_id=project.id)

    if request.method == 'POST':
        project_title = project.title  # 메시지용
        project.delete()
        messages.success(request, f"프로젝트 “{project_title}”이(가) 성공적으로 삭제되었습니다.")
        return redirect('label_studio:project_list')  # 삭제 후 이동할 페이지
    else:
        # POST 외 접근일 경우 편집 페이지로 리다이렉트
        return redirect('label_studio:modify_project', project_id=project.id)

@require_POST
def sync_workers_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    selected_ids = set(map(int, request.POST.getlist("workers")))

    # 현재 등록된 작업자 ID
    current_ids = set(project.workers.values_list('id', flat=True))

    to_add = selected_ids - current_ids
    to_remove = current_ids - selected_ids

    added, removed = 0, 0

    for user_id in to_add:
        user = get_object_or_404(User, id=user_id)
        _, created = Assignment.objects.get_or_create(project=project, worker=user)
        if created:
            added += 1

    for user_id in to_remove:
        Assignment.objects.filter(project=project, worker_id=user_id).delete()
        removed += 1

    messages.success(request, f"작업자 {added}명 추가, {removed}명 제거되었습니다.")
    return redirect("label_studio:project_detail", project_id=project_id)


@login_required
def project_create_view(request):
    if request.method == 'POST':
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            # 1) 프로젝트 생성
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            form.save_m2m()

            # 2) 작업자 할당
            for user in form.cleaned_data['workers']:
                Assignment.objects.get_or_create(project=project, worker=user)

            # 3) 라벨 삽입
            if project.task_type == 'hierarchy':
                raw_json = request.POST.get('label_hierarchy', '')
                try:
                    data = json.loads(raw_json)
                    if not isinstance(data, list):
                        raise ValueError('JSON 최상위 구조는 리스트여야 합니다.')
                except Exception as e:
                    messages.error(request, f'계층형 JSON 오류: {e}')
                    users = User.objects.all()
                    return render(request, 'label_studio/create_project.html', {
                        'form': form,
                        'users': users,
                        'selected_worker_ids': request.POST.getlist('workers'),
                        'hierarchy_error': str(e),
                    })

                def recurse(nodes, parent=None):
                    for idx, node in enumerate(nodes):
                        name = node.get('name')
                        if not name:
                            continue
                        lbl = Label.objects.create(
                            project=project,
                            name=name.strip(),
                            label_type='hierarchy',
                            description=node.get('description', '').strip(),
                            order=idx,
                            parent=parent
                        )
                        children = node.get('children')
                        if isinstance(children, list):
                            recurse(children, parent=lbl)

                recurse(data)

            else:
                # 기존 classification/summary/evaluation/compare 처리
                label_names   = request.POST.getlist('label_name')
                label_descs   = request.POST.getlist('label_desc')
                label_orders  = request.POST.getlist('label_order')
                label_options = request.POST.getlist('label_options')

                for i, name in enumerate(label_names):
                    if not name.strip():
                        continue
                    desc = label_descs[i].strip() if i < len(label_descs) else ''
                    if project.task_type == 'evaluation' and i < len(label_options):
                        desc += label_options[i]
                    Label.objects.create(
                        project=project,
                        name=name.strip(),
                        label_type=project.task_type,
                        description=desc,
                        order=int(label_orders[i]) if (i < len(label_orders) and label_orders[i].isdigit()) else None
                    )

            return redirect('label_studio:index')
    else:
        form = ProjectCreateForm()

    users = User.objects.all()
    return render(request, 'label_studio/create_project.html', {
        'form': form,
        'users': users,
        'selected_worker_ids': request.POST.getlist('workers') if request.method == 'POST' else []
    })

@require_POST
def add_label_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    name = request.POST.get('name')
    label_type = request.POST.get('label_type')
    order = request.POST.get('order')
    description = request.POST.get('description')

    if not name or not label_type:
        messages.error(request, "레이블명과 타입은 필수입니다.")
        return redirect('label_studio:project', project_id=project.id)

    try:
        label = Label.objects.create(
            project=project,
            name=name.strip(),
            label_type=label_type.strip(),
            description=description.strip() if description else None,
            order=int(order) if order else None,
        )
        messages.success(request, f"레이블 '{label.name}' 이(가) 추가되었습니다.")
    except Exception as e:
        messages.error(request, f"레이블 추가 중 오류: {str(e)}")

    return redirect('label_studio:project', project_id=project.id)

@require_POST
def delete_label_view(request, project_id, label_id):
    label = get_object_or_404(Label, id=label_id, project_id=project_id)
    label_name = label.name
    label.delete()
    messages.success(request, f"레이블 '{label_name}' 이(가) 삭제되었습니다.")
    return redirect('label_studio:project', project_id=project_id)

def reorder_input_data(project):
    inputs = InputData.objects.filter(project=project, is_active=True).order_by('order', 'id')
    for idx, input_data in enumerate(inputs, start=1):
        if input_data.order != idx:
            input_data.order = idx
            input_data.save(update_fields=['order'])

@require_POST
def delete_input_view(request, project_id, input_id):
    input_data = get_object_or_404(InputData, id=input_id, project_id=project_id)
    input_data.delete()
    reorder_input_data(input_data.project)  # 🧠 삭제 후 자동 정렬
    messages.success(request, "입력 데이터가 삭제되고 정렬되었습니다.")
    return redirect("label_studio:project_detail", project_id=project_id)

@require_POST
def upload_input_data_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    upload_file = request.FILES.get('uploadFile')

    if not upload_file:
        messages.error(request, "파일이 선택되지 않았습니다.")
        return redirect('label_studio:project', project_id=project.id)

    try:
        # 마지막 order 찾기
        last_order = InputData.objects.filter(project=project).aggregate(max_order=Max("order"))["max_order"] or 0
        lines = upload_file.read().decode("utf-8").splitlines()
        created_count = 0

        for i, line in enumerate(lines):
            data = json.loads(line.strip())
            InputData.objects.create(
                project=project,
                data=data,
                order=last_order + i + 1
            )
            created_count += 1

        messages.success(request, f"{created_count}개의 입력 데이터가 성공적으로 업로드되었습니다.")
    except Exception as e:
        messages.error(request, f"업로드 중 오류가 발생했습니다: {str(e)}")

    return redirect('label_studio:project', project_id=project.id)

TEMPLATE_MAP = {
    'classification': 'label_studio/classifier.html',
    'summary'       : 'label_studio/summary.html',
    'evaluation'    : 'label_studio/evaluation.html',
    'compare'       : 'label_studio/compare.html',
    'hierarchy'     : 'label_studio/hierarchy.html',    # 추가
}

FIELD_NAME_MAP = {
    'classification': 'label',
    'summary'       : 'summary',
    'evaluation'    : 'dict',
    'compare'       : 'label',
    'hierarchy'     : 'dict',                           # 추가
}

def get_work_detail(project, user):
    # 1) 전체/완료/남은 수 계산
    total     = InputData.objects.filter(project=project, is_active=True).count()
    completed = WorkResult.objects.filter(project=project, worker=user) \
                                .values_list("input_data_id", flat=True) \
                                .distinct().count()
    remaining = total - completed

    # 2) 이미 작업한 결과
    work_results = (
        WorkResult.objects
                .filter(project=project, worker=user)
                .select_related('input_data')
                .order_by('input_data__order')
    )

    # 3) 남은 InputData 목록
    done_ids = [r.input_data_id for r in work_results]
    remaining_inputs = (
        InputData.objects
                .filter(project=project, is_active=True)
                .exclude(id__in=done_ids)
                .order_by('order')
    )

    return {
            "project": project,
            "total": total,
            "completed": completed,
            "remaining": remaining,
            "work_results": work_results,
            "remaining_inputs": remaining_inputs,
        }


@login_required
def move_work_page_view(request, project):
    field_name = FIELD_NAME_MAP.get(project.task_type)
    if not field_name:
        return render(request, "label_studio/unsupported_task.html", {'project': project})

    ctx = get_work_context(request, project, task_field_name=field_name)
    if ctx is None:
        return render(request, "label_studio/work_complete.html", {'project': project})

    template = TEMPLATE_MAP[project.task_type]
    ctx.update({'project': project})

    if project.task_type == 'classification':
        ctx.update({
            'labels': Label.objects.filter(project=project).order_by('order'),
            'selected_label': ctx.pop('result_value'),
        })

    elif project.task_type == 'summary':
        ctx.update({'selected_summary': ctx.pop('result_value')})

    elif project.task_type == 'evaluation':
        ctx.update({
            'labels': Label.objects.filter(project=project).order_by('order'),
            'selected_scores': ctx.pop('result_value'),
        })

    elif project.task_type == 'hierarchy':
        # Label 인접리스트로 노드 트리를 빌드 (위에서 설명했던 로직 그대로)
        all_labels = Label.objects.filter(project=project).order_by('order','id')
        nodes = {lbl.id: {'id':lbl.id,'name':lbl.name,'children':[]} for lbl in all_labels}
        roots = []
        for lbl in all_labels:
            if lbl.parent_id:
                nodes[lbl.parent_id]['children'].append(nodes[lbl.id])
            else:
                roots.append(nodes[lbl.id])

        # 기존 저장값 꺼내오기
        selected_path = ctx.get('selected_path', [])
        ctx.update({
        'hierarchy': roots,
        'selected_path': selected_path,
        })

    else:  # compare
        ctx.update({'selected_output': ctx.pop('result_value')})

    return render(request, template, ctx)

@login_required
def work_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    user = request.user
    # 1) 권한 체크
    if not project.workers.filter(id=request.user.id).exists():
        return render(request, "label_studio/no_permission.html", status=403)

    # 2) data_order GET 파라미터 유무로 분기
    data_order = request.GET.get('data_order')
    if not data_order:
        return render(request, "label_studio/worker.html", get_work_detail(project, user))
    
    return move_work_page_view(request, project)



@require_POST
@login_required
def submit_work_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not project.workers.filter(id=request.user.id).exists():
        return render(request, "label_studio/no_permission.html", status=403)

    input_id = request.POST.get("input_id")
    input_data = get_object_or_404(InputData, id=input_id, project_id=project_id)

    task = project.task_type
    if task == "classification":
        result_data = {"label": request.POST.get("label")}
    elif task == "summary":
        result_data = {"summary": request.POST.get("summary")}
    elif task == "evaluation":
        labels = Label.objects.filter(project=project).order_by("order")
        result_data = {"label":{
            lbl.name: request.POST.get(f"score_{lbl.name}")
            for lbl in labels
            if request.POST.get(f"score_{lbl.name}")
        }}
    elif task == "hierarchy":
        # form에서 name="path" 로 온 모든 값을 리스트로 가져옵니다
        # 1) POST 로 넘어온 JSON 문자열 파싱
        raw = request.POST.get('path', '[]')
        try:
            path_ids = json.loads(raw)
            # 문자열로 넘어오는 경우도 int 로 변환
            path_ids = [int(x) for x in path_ids]
        except Exception:
            path_ids = []

        # 2) Label 모델에서 id → name 매핑
        labels = Label.objects.filter(id__in=path_ids)
        id_to_name = {lbl.id: lbl.name for lbl in labels}

        # 3) 순서를 유지하며 이름 리스트로 변환
        path_names = [id_to_name[i] for i in path_ids if i in id_to_name]

        # 4) result_data 에 이름 리스트 저장
        result_data = {'label': path_names}
    else:  # compare
        result_data = {"label": request.POST.get("selected_output")}

    # 저장
    save_result(request, project, input_data, result_data)

    # 다음으로 이동
    next_order = request.POST.get("data_order")
    base = reverse("label_studio:work_entry", args=[project_id])
    if next_order:
        return redirect(f"{base}?data_order={next_order}")
    return redirect(base)

def save_result(request, project, input_data, result_data, status="submitted"):
    comment = request.POST.get("comment", "")
    WorkResult.objects.update_or_create(
        project=project,
        worker=request.user,
        input_data=input_data,
        defaults={
            "result" : result_data,
            "comment": comment,
            "status" : status,
        }
    )

def get_work_context(request, project, task_field_name):
    user       = request.user
    inputs     = list(InputData.objects.filter(project=project, is_active=True).order_by("order"))
    total      = len(inputs)
    if total == 0:
        return None

    # 1) data_order 파라미터가 있으면 그 순번의 데이터를 가져온다
    data_order = request.GET.get("data_order")
    if data_order:
        try:
            order = int(data_order)
            input_data = next((i for i in inputs if i.order == order), None)
        except (ValueError, StopIteration):
            input_data = None
    else:
        # 2) 아직 라벨하지 않은 첫 항목
        done_ids   = WorkResult.objects.filter(project=project, worker=user).values_list("input_data_id", flat=True)
        remaining  = [i for i in inputs if i.id not in done_ids]
        input_data = remaining[0] if remaining else inputs[-1]

    if not input_data:
        return None

    # 기존 저장된 결과가 있으면 꺼내오고
    
    existing = WorkResult.objects.filter(project=project, worker=user, input_data=input_data).first()
    if existing:
        if task_field_name == "dict":
            result_value = existing.result
        else:
            result_value = existing.result.get(task_field_name)
        # — 기존에 선택된 경로(name 배열) → id 배열로 변환 —
        raw_labels = existing.result.get('label', [])  # e.g. ["대분류B","중분류B1","소분류B1-1"]
        # 프로젝트 전체 hierarchy 라벨을 미리 가져왔다고 가정
        labels = Label.objects.filter(project=project, label_type='hierarchy')
        name_to_id = {lbl.name: lbl.id for lbl in labels}
        selected_path = [ name_to_id[name] for name in raw_labels if name_to_id.get(name) ]
    elif "summary" in input_data.data:
        result_value = input_data.data["summary"]
        selected_path = []
    elif "label" in input_data.data:
        default_value = input_data.data
        if task_field_name == "dict":
            result_value = default_value
        else:
            result_value = default_value['label']
            
        # — 기존에 선택된 경로(name 배열) → id 배열로 변환 —
        raw_labels = default_value.get('label', [])#default_value.get('label', [])  # e.g. ["대분류B","중분류B1","소분류B1-1"])
        # 프로젝트 전체 hierarchy 라벨을 미리 가져왔다고 가정
        labels = Label.objects.filter(project=project, label_type='hierarchy')
        name_to_id = {lbl.name: lbl.id for lbl in labels}
        selected_path = [ name_to_id[name] for name in raw_labels if name_to_id.get(name) ]
    else:
        result_value = ""
        selected_path = []

    idx   = inputs.index(input_data) + 1
    done  = WorkResult.objects.filter(project=project, worker=user).values_list("input_data_id", flat=True).distinct().count()
    prog  = int(done / total * 100) if total else 0
    is_last = (idx == total)

    # Assignment 업데이트
    assignment, _ = Assignment.objects.get_or_create(project=project, worker=user)
    assignment.progress     = prog
    assignment.status       = "completed" if prog == 100 else "in_progress"
    assignment.last_updated = timezone.now()
    assignment.save()
    
    return {
        "input_data": input_data,
        "result_value": result_value,
        "progress": prog,
        "current_index": idx,
        "total_inputs": total,
        "is_last_input": is_last,
        "selected_path": selected_path,
        "comment": existing.comment if existing else "",
    }

TEST = """
CTranslate2 Backend for Triton Inference Server
This is a backend based on CTranslate2 for NVIDIA's Triton Inference Server, which can be used to deploy translation and language models supported by CTranslate2 on Triton with both CPU and GPU capabilities.

It supports ragged and dynamic batching and setting of (a subset of) CTranslate decoding parameters in the model config.

Building
Make sure to have cmake installed on your system.

Build and install CTranslate2: https://opennmt.net/CTranslate2/installation.html#compile-the-c-library
Build the backend
mkdir build && cd build
export BACKEND_INSTALL_DIR=$(pwd)/install
cmake .. -DCMAKE_BUILD_TYPE=Release -DTRITON_ENABLE_GPU=1 -DCMAKE_INSTALL_PREFIX=$BACKEND_INSTALL_DIR
make install
This builds the backend into $BACKEND_INSTALL_DIR/backends/ctranslate2.

Setting up the backend
First install the pip package to convert models: pip install ctranslate2. Then create a model repository, which consists of a configuration (config.pbtxt) and the converted model.

For example for the Helsinki-NLP/opus-mt-en-de HuggingFace transformer model, create a new directory e.g. mkdir $MODEL_DIR/opus-mt-en-de. The model needs to be moved into a directory called model that is nested in a folder specifying a numerical version of the model:"""

def guideline_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    guideline_path = project.guideline_path
    if not guideline_path or not os.path.exists(guideline_path):
        return HttpResponse(TEST, content_type="text/plain")

    with open(guideline_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    return HttpResponse(content, content_type="text/plain")