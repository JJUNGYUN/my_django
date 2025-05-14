from django.contrib.auth import logout, authenticate, login
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from common.forms import UserForm
from playground.models import Playground
from models.models import LM_models
from label_studio.models import Project
from datasets_repo.models import Datasets

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