from django import forms
from model_dashboard.models import Benchmark, BenchmarkResult
from datasets_repo.models import Datasets
from models.models import LM_models

class dashboardForm(forms.ModelForm):
    dataset_name = forms.ModelChoiceField(
        queryset=Datasets.objects.all(),
        to_field_name='name',  # 'id'가 아니라 'name' 기준으로 매칭
    )
    class Meta:
        model = Benchmark
        fields = ['benchmark_name','dataset_name', 'metrics','dataset_version']


class evalresultForm(forms.ModelForm):
    model_name = forms.ModelChoiceField(
        queryset=LM_models.objects.all(),
        to_field_name='name',  # 'id'가 아니라 'name' 기준으로 매칭
    )
    benchmark_name = forms.ModelChoiceField(
        queryset=Benchmark.objects.all(),
        to_field_name='benchmark_name',  # 'id'가 아니라 'name' 기준으로 매칭
    )
    class Meta:
        model = BenchmarkResult
        fields = ['model_name','benchmark_name', 'evaluate_result']