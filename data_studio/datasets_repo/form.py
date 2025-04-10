from django import forms
from datasets_repo.models import Datasets

class datasetlForm(forms.ModelForm):
    class Meta:
        model = Datasets
        fields = ['name', 'task', 'tag','dataset_path']