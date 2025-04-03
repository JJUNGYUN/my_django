from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class LM_models(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    parameter_size = models.CharField(max_length=64)
    weight_path = models.CharField(max_length=128)
    tag = models.JSONField(default=list)
    file_size = models.CharField(max_length=64)
    create_date = models.DateTimeField()
    # 베이스 모델도 추가하고 싶어라
    #연관모델 추가하고 싶어라~
    
    def __str__(self):
        return self.name
"""
from models.models import LM_models
from django.contrib.auth.models import User

users = User.objects.get(username="3548")

q=LM_models( \
author=users, \
name="bert-base-uncased", \
parameter_size="110M", \
weight_path="/root/workspace/mystudio/Mydjango/model_repo/bert-base-uncased/", \
tag=["bert","nlp","encoder"], \
file_size="420M", \
create_date=timezone.now()\
)

q.save()
"""