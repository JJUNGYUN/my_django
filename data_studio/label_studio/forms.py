from django import forms
from .models import Project, Label
from django.contrib.auth import get_user_model

User = get_user_model()

class ProjectCreateForm(forms.ModelForm):
    workers = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'multiple': True})
    )
    
    class Meta:
        model = Project
        fields = ['title', 'description', 'start_date', 'end_date', 'task_type', 'workers']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'task_type': forms.Select(choices=[
                ('binary', '이진 분류'),
                ('multiclass', '다중 클래스'),
                ('summary', '요약')
            ]),
        }
