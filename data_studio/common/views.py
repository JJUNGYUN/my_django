from django.contrib.auth import logout, authenticate, login
from django.shortcuts import redirect, render
from common.forms import UserForm

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