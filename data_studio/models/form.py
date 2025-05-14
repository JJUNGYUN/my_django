from django import forms
from models.models import LM_models

class modelForm(forms.ModelForm):
    class Meta:
        model = LM_models
        fields = ['name', 'weight_path']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'tag' in self.fields and self.instance:
            self.fields['tag'].initial = self.instance.tag