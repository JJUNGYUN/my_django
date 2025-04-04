from django import forms
from models.models import LM_models

class modelForm(forms.ModelForm):
    class Meta:
        model = LM_models
        fields = ['name', 'parameter_size', 'tag', 'weight_path']