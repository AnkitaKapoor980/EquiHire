from django.db import models
from django.contrib.postgres.fields import ArrayField
from pgvector.django import VectorField
from accounts.models import User


class Resume(models.Model):
    """Resume model with parsed data and vector embedding."""
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500, help_text='Path in MinIO storage')
    file_size = models.IntegerField(help_text='File size in bytes')
    file_type = models.CharField(max_length=50, help_text='MIME type (e.g., application/pdf)')
    
    # Parsed data from parser service
    parsed_data = models.JSONField(default=dict, blank=True, help_text='Structured data from resume parser')
    raw_text = models.TextField(blank=True, null=True, help_text='Extracted raw text')
    
    # Extracted entities
    skills = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    education = ArrayField(models.CharField(max_length=200), default=list, blank=True)
    experience_years = models.IntegerField(null=True, blank=True)
    certifications = ArrayField(models.CharField(max_length=200), default=list, blank=True)
    
    # ML embedding
    embedding = VectorField(dimensions=384, null=True, blank=True, help_text='Sentence-BERT embedding')
    
    # Metadata
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'resumes'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['candidate', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.candidate.email} - {self.file_name}"


class CandidateProfile(models.Model):
    """Extended candidate profile information."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidate_profile')
    summary = models.TextField(blank=True, null=True)
    current_position = models.CharField(max_length=200, blank=True, null=True)
    current_company = models.CharField(max_length=200, blank=True, null=True)
    years_of_experience = models.IntegerField(null=True, blank=True)
    education_level = models.CharField(
        max_length=50,
        choices=[
            ('high-school', 'High School'),
            ('bachelor', "Bachelor's Degree"),
            ('master', "Master's Degree"),
            ('phd', 'PhD'),
            ('other', 'Other'),
        ],
        blank=True,
        null=True
    )
    preferred_locations = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    preferred_salary_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    preferred_salary_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    portfolio_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'candidate_profiles'
    
    def __str__(self):
        return f"Profile: {self.user.email}"

