from django import forms
from playground.models import Playground
from models.models import LM_models

class PlaygroundForm(forms.ModelForm):
    llm_model = forms.CharField(label='모델 이름')

    class Meta:
        model = Playground
        fields = ['playtype', 'llm_model']

    def clean_llm_model(self):
        model_name = self.cleaned_data['llm_model']
        try:
            return LM_models.objects.get(name=model_name)
        except LM_models.DoesNotExist:
            raise forms.ValidationError("입력한 모델셋이 존재하지 않습니다.")