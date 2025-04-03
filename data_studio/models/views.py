from .models import LM_models
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import HttpResponseNotAllowed
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.safestring import mark_safe
from django import template

import markdown
import os

register = template.Library()


# Create your views here.
def index(request):
    page = request.GET.get('page','1')  
    models_list = LM_models.objects.order_by('id')
    paginator = Paginator(models_list, 10)
    page_obj = paginator.get_page(page)
    context = {'models_list': page_obj}
    
    return render(request, 'models/model_list.html', context)

def detail(request, question_id):
    model = get_object_or_404(LM_models, pk=question_id)
    model_path = model.weight_path

    with open(os.path.join(model_path,"README.md")) as f:
        readme = ''.join(f.readlines())
    context = {'model':model, 'readme': readme}

    return render(request, 'models/model_detail.html',context)