from django.db import models
from django.contrib.postgres.fields import ArrayField
from pgvector.django import VectorField
from accounts.models import User


class JobDescription(models.Model):
    """Job posting model with vector embedding for matching."""
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    location = models.CharField(max_length=200, blank=True, null=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    employment_type = models.CharField(
        max_length=50,
        choices=[
            ('full-time', 'Full Time'),
            ('part-time', 'Part Time'),
            ('contract', 'Contract'),
            ('internship', 'Internship'),
        ],
        default='full-time'
    )
    required_skills = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    embedding = VectorField(dimensions=384, null=True, blank=True)  # Sentence-BERT embedding
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'job_descriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.posted_by.email}"


class Application(models.Model):
    """Application model linking candidates to jobs."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('hired', 'Hired'),
    ]
    
    job = models.ForeignKey(JobDescription, on_delete=models.CASCADE, related_name='applications')
    resume = models.ForeignKey('candidates.Resume', on_delete=models.CASCADE, related_name='applications')
    score = models.FloatField(null=True, blank=True, help_text='Matching score from ML model')
    ranking = models.IntegerField(null=True, blank=True, help_text='Ranking position among all applicants')
    fairness_metrics = models.JSONField(default=dict, blank=True, help_text='Bias detection metrics')
    explanation = models.JSONField(default=dict, blank=True, help_text='SHAP explanation values')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'applications'
        unique_together = ['job', 'resume']
        ordering = ['-score', '-created_at']
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['job', 'score']),
        ]
    
    def __str__(self):
        return f"{self.resume.candidate.email} -> {self.job.title}"

