from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import HttpResponseNotAllowed
from .form import QuestionForm, AnswerForm
from .models import Question
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def index(request):
    page = request.GET.get('page','1')
    question_list = Question.objects.order_by('-create_date')
    paginator = Paginator(question_list, 10)
    page_obj = paginator.get_page(page)
    context = {'question_list': page_obj}
    return render(request, 'pybo/question_list.html', context)

def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    context = {'question':question}

    return render(request, 'pybo/question_detail.html',context)

@login_required(login_url='common:login')
def answer_create(request, question_id):
    question = get_object_or_404(Question, pk=question_id)

    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.create_date = timezone.now()
            answer.question = question
            answer.author = request.user
            answer.save()
           
            return redirect('pybo:detail', question_id=question.id)
    else:
        return HttpResponseNotAllowed('Only POST is possible.')
    context = {'question':question, 'form':form}
    return render(request, 'pybo/question_detail.html', context)

@login_required(login_url='common:login')
def question_create(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.create_date = timezone.now()
            question.author = request.user
            question.save()
            return redirect('pybo:index')
    else:
        form = QuestionForm()
    context = {'form':form}
    return render(request, 'pybo/question_form.html', context)

def question_modify(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if request.user != question.author:
        messages.error(request, '수정 권한 없음')
        return redirect('pybo:detail',question_id=question.id)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            question = form.save(commit=False)
            question.create_date = timezone.now()
            question.author = request.user
            question.save()
            return redirect('pybo:detail',question_id=question.id)
    else:
        form = QuestionForm(instance=question)

    context = {'form':form}
    return render(request, 'pybo/question_form.html', context)

@login_required(login_url='common:login')
def question_delete(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if request.user != question.author:
        messages.error(request, '삭제 권한 없음')
        return redirect('pybo:detail',question_id=question.id)
    question.delete()
    return redirect('pybo:index')


def test(request):
    import os
    from datasets_repo.utils import get_file_info_from_dir
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
    else:
        path = '/'
        if os.path.isdir(path):
            file_list = get_file_info_from_dir(path)



    context = {'file_list':file_list, 'path':path}
    return render(request, 'test/list_test.html', context)


