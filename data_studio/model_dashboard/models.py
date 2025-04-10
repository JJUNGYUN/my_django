from django.db import models
from models.models import LM_models
from datasets_repo.models import Datasets
from django.contrib.auth.models import User

class Benchmark(models.Model):
    """
    특정 LLM 모델의 벤치마크 평가 결과를 저장하는 모델.
    """
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    benchmark_name = models.CharField(max_length=255, unique=True,  help_text="평가 벤치마크 이름 (예: MMLU)")
    metrics = models.JSONField(blank=True, null=True, help_text="측정 지표 예: {'BLEU': 0.75, 'ROUGE': 0.82, 'ACC': 0.90}")
    dataset_version = models.CharField(max_length=100, blank=True, null=True, help_text="데이터셋 버전")
    dataset_name =  models.ForeignKey(Datasets, on_delete=models.CASCADE, max_length=255, help_text="평가 벤치마크 이름 (예: MMLU)")
    tag = models.CharField(max_length=512)

    def __str__(self):
        return f"{self.benchmark_name}"


"""
from model_dashboard.models import Benchmark
from django.contrib.auth.models import User
from django.utils import timezone

from datasets_repo.models import Datasets

users = User.objects.get(username="3548")

q=Benchmark( \
author=users, \
benchmark_name="test1", \
metrics="{'F-1', 'Recall', 'BLEU'}", \
dataset_version="250408-test", \
tag="bert,nlp,encoder", \
dataset_name=Datasets.objects.get(name="korean-ciper"), \
)
q.save()

"""


class BenchmarkResult(models.Model):
    """
    특정 LLM 모델의 벤치마크 평가 결과를 저장하는 모델.
    """
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    llm_model = models.ForeignKey(
        LM_models,
        on_delete=models.CASCADE,
        related_name='model_name',
        help_text="평가된 모델"
    )
    benchmark_name = models.ForeignKey(Benchmark, on_delete=models.CASCADE, max_length=255, help_text="평가 벤치마크 이름 (예: MMLU)")
    metrics = models.JSONField(blank=True, null=True, help_text="측정 지표 예: {'BLEU': 0.75, 'ROUGE': 0.82, 'ACC': 0.90}")
    dataset_version = models.CharField(max_length=100, blank=True, null=True, help_text="데이터셋 버전")
    date_evaluated = models.DateField(blank=True, null=True, help_text="평가한 날짜")
    evaluate_result = models.JSONField(blank=True, null=True, help_text="평가 결과 샘플 파일")
    def __str__(self):
        return f"{self.llm_model.name} - {self.benchmark_name}"
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['llm_model', 'benchmark_name'], name='unique_model_per_benchmark')
        ]
"""
from model_dashboard.models import Benchmark, BenchmarkResult
from django.contrib.auth.models import User
from django.utils import timezone

from datasets_repo.models import Datasets
from models.models import LM_models

users = User.objects.get(username="3548")

q=BenchmarkResult( \
author=users, \
llm_model=LM_models.objects.get(name="test1"), \
benchmark_name=Benchmark.objects.get(benchmark_name="test1"), \
metrics="{'F-1':1.0, 'Recall':0.98, 'BLEU':32.4}", \
date_evaluated=timezone.now(), \
evaluate_result="[{'입력':'1+1=','출력':'2'}, {'입력':'2+2=','출력':'4'}]"\
)
q.save()

"""