from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Project(models.Model):
    STATUS_CHOICES = [
        ('in_progress', '작업중'),
        ('completed', '완료'),
        ('stopped', '중단'),
    ]

    id = models.BigAutoField(primary_key=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    task_type = models.CharField(max_length=50)  # ex) 'binary', 'multiclass', 'summary'
    task_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')  # ✅ 추가
    guideline_path = models.CharField(max_length=512, blank=True, null=True)  # ✅ 추가: 가이드라인 파일 경로
    workers = models.ManyToManyField(User, through='Assignment', related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title



class Assignment(models.Model):
    id = models.BigAutoField(primary_key=True)
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='assignments')
    progress = models.PositiveIntegerField(default=0)  # 0~100
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('stopped', 'Stopped'),
        ('pending', 'Pending'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('worker', 'project')  # 같은 작업자가 같은 프로젝트에 중복 등록 불가

    def __str__(self):
        return f"{self.worker} - {self.project}"


class InputData(models.Model):
    id = models.BigAutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='input_data')
    data = models.JSONField()  # Django 3.1+ 에서 기본 지원
    order = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['project', 'order']),
        ]

    def __str__(self):
        return f"Input {self.id} for Project {self.project_id}"


class WorkResult(models.Model):
    id = models.BigAutoField(primary_key=True)
    input_data = models.ForeignKey(InputData, on_delete=models.CASCADE, related_name='work_results')
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='work_results')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='work_results')
    result = models.JSONField()
    comment = models.TextField(blank=True, null=True)  # ✅ 추가: 작업자 코멘트 필드
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('input_data', 'worker')  # 하나의 input에 대해 한 작업자 결과 하나
        indexes = [
            models.Index(fields=['input_data']),
            models.Index(fields=['project']),
        ]

    def __str__(self):
        return f"Result for Input {self.input_data_id} by Worker {self.worker_id}"


class Label(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='labels')
    name = models.CharField(max_length=100)
    label_type = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(blank=True, null=True)
    parent      = models.ForeignKey(
                    'self',
                    on_delete=models.CASCADE,
                    null=True,
                    blank=True,
                    related_name='children'
                  )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['project']),
        ]

    def __str__(self):
        return f"{self.name} ({self.label_type})"
