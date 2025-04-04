from .models import LM_models
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
from django import template

from .form import modelForm
from .utils import get_file_info_from_dir

import os

register = template.Library()


# Create your views here.
def index(request):
    page = request.GET.get('page','1')  
    models_list = LM_models.objects.order_by('id')
    paginator = Paginator(models_list, 20)
    page_obj = paginator.get_page(page)
    context = {'models_list': page_obj}

    return render(request, 'models/model_list.html', context)

def detail(request, question_id):
    model = get_object_or_404(LM_models, pk=question_id)
    model_path = model.weight_path

    if os.path.isfile(os.path.join(model_path,"README.md")):
        with open(os.path.join(model_path,"README.md")) as f:
            readme = ''.join(f.readlines())
    else:
        readme = 'README.md가 없어요'

    if model.weight_path and os.path.isdir(model.weight_path):
        file_list = get_file_info_from_dir(model.weight_path)
                                                   
    context = {'model':model, 'readme': readme, 'file_list':file_list}


    return render(request, 'models/model_detail.html',context)

@login_required(login_url='common:login')
def new_model(request):
    file_list = []
    if request.method == 'POST':
        form = modelForm(request.POST)
        if form.is_valid():
            if 'save' in request.POST:
                model = form.save(commit=False)
                model.create_date = timezone.now()
                model.author = request.user
                model.file_size = "110MB"
                model.save()
                return redirect('models:index')
        elif 'preview' in request.POST:
            weight_path = form.cleaned_data.get('weight_path')
            if weight_path and os.path.isdir(weight_path):
                file_list = get_file_info_from_dir(weight_path)
            else:
                file_list = ['weight_path must be directory path']
            
    else:
        form = LM_models()

    context = {'form':form, 'file_list':file_list}
    return render(request, 'models/new_model.html', context)