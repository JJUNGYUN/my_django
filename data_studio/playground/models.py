from django.db import models
from django.contrib.auth.models import User
from models.models import LM_models

# Create your models here.
class Playground(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    llm_model = models.ForeignKey(
        LM_models,
        on_delete=models.CASCADE
    )
    playtype = models.CharField(max_length=128)
    server = models.CharField(max_length=128)
    gpu_index = models.CharField(max_length=128)
    docker_name = models.CharField(max_length=128)
    triton_port = models.CharField(max_length=16)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=32)

    def __str__(self):
        return  f"{self.llm_model}-{self.playtype}"
    
    class Meta:
        app_label = 'playground'
        constraints = [
            models.UniqueConstraint(fields=['llm_model', 'playtype'], name='unique_model_per_playground')
        ]