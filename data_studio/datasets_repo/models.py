from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Datasets(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(unique=True,max_length=128)
    modality = models.CharField(max_length=128)
    tag = models.CharField(max_length=512)
    task = models.CharField(max_length=512)
    dataset_path = models.CharField(max_length=512)
    file_size = models.CharField(max_length=64)
    create_date = models.DateTimeField()

    def __str__(self):
        return self.name
    
    class Meta:
        app_label = 'datasets'
"""
from models.models import LM_models
from django.contrib.auth.models import User
from django.utils import timezone

users = User.objects.get(username="3548")

q=LM_models( \
author=users, \
name="bert-base-uncased", \
parameter_size="110M", \
weight_path="/root/workspace/mystudio/Mydjango/model_repo/bert-base-uncased/", \
tag="bert,nlp,encoder", \
file_size="420M", \
create_date=timezone.now()\
)
q.save()

"""