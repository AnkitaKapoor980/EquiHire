"""HTML views for jobs app."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from .models import JobDescription, Application
from candidates.models import Resume
import requests
from django.conf import settings


@login_required
def job_list_view(request):
    """List all jobs."""
    jobs = JobDescription.objects.filter(is_active=True).order_by('-created_at')
    
    # Filter by search query
    search = request.GET.get('search', '')
    if search:
        jobs = jobs.filter(
            models.Q(title__icontains=search) |
            models.Q(description__icontains=search) |
            models.Q(requirements__icontains=search)
        )
    
    context = {'jobs': jobs, 'search': search}
    return render(request, 'jobs/job_list.html', context)


@login_required
def job_detail_view(request, pk):
    """Job detail view."""
    job = get_object_or_404(JobDescription, pk=pk)
    
    # Get applications for this job (if recruiter)
    applications = None
    if request.user.is_recruiter() and job.posted_by == request.user:
        applications = Application.objects.filter(job=job).order_by('-score', '-created_at')
    
    # Check if candidate has already applied
    has_applied = False
    if request.user.is_candidate():
        has_applied = Application.objects.filter(
            job=job,
            resume__candidate=request.user
        ).exists()
    
    context = {
        'job': job,
        'applications': applications,
        'has_applied': has_applied,
        'can_apply': request.user.is_candidate() and not has_applied
    }
    return render(request, 'jobs/job_detail.html', context)


@login_required
def job_create_view(request):
    """Create a new job posting."""
    if not request.user.is_recruiter():
        messages.error(request, 'Only recruiters can post jobs.')
        return redirect('dashboard:recruiter_dashboard')
    
    if request.method == 'POST':
        job = JobDescription.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            requirements=request.POST.get('requirements'),
            location=request.POST.get('location', ''),
            employment_type=request.POST.get('employment_type', 'full-time'),
            salary_min=request.POST.get('salary_min') or None,
            salary_max=request.POST.get('salary_max') or None,
            posted_by=request.user,
            is_active=True
        )
        
        # Generate embedding
        try:
            text = f"{job.title} {job.description} {job.requirements}"
            response = requests.post(
                f"{settings.MATCHER_SERVICE_URL}/api/embed",
                json={'text': text},
                timeout=10
            )
            if response.status_code == 200:
                embedding = response.json().get('embedding')
                if embedding:
                    job.embedding = embedding
                    job.save(update_fields=['embedding'])
        except Exception as e:
            pass  # Embedding can be generated later
        
        messages.success(request, 'Job posted successfully!')
        return redirect('jobs:job-detail', pk=job.id)
    
    return render(request, 'jobs/job_form.html', {'form_type': 'create'})


@login_required
def application_list_view(request):
    """List applications."""
    if request.user.is_recruiter():
        applications = Application.objects.filter(
            job__posted_by=request.user
        ).select_related('job', 'resume', 'resume__candidate').order_by('-created_at')
    else:
        applications = Application.objects.filter(
            resume__candidate=request.user
        ).select_related('job', 'resume').order_by('-created_at')
    
    context = {'applications': applications}
    return render(request, 'jobs/application_list.html', context)


@login_required
def application_detail_view(request, pk):
    """Application detail view."""
    application = get_object_or_404(Application, pk=pk)
    
    # Check permissions
    if request.user.is_recruiter() and application.job.posted_by != request.user:
        messages.error(request, 'Access denied.')
        return redirect('jobs:application-list')
    if request.user.is_candidate() and application.resume.candidate != request.user:
        messages.error(request, 'Access denied.')
        return redirect('jobs:application-list')
    
    context = {'application': application}
    return render(request, 'jobs/application_detail.html', context)

