"""HTML views for jobs app."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from .models import JobDescription, Application
from candidates.models import Resume
import requests
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)


def job_list_view(request):
    """List all jobs. Allow unauthenticated users to view jobs."""
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


def job_detail_view(request, pk):
    """Job detail view. Allow unauthenticated users to view job details."""
    job = get_object_or_404(JobDescription, pk=pk)
    
    # Get applications for this job (if recruiter and authenticated)
    applications = None
    if request.user.is_authenticated and request.user.is_recruiter() and job.posted_by == request.user:
        applications = Application.objects.filter(job=job).order_by('-score', '-created_at')
    
    # Check if candidate has already applied
    has_applied = False
    if request.user.is_authenticated and request.user.is_candidate():
        has_applied = Application.objects.filter(
            job=job,
            resume__candidate=request.user
        ).exists()
    
    context = {
        'job': job,
        'applications': applications,
        'has_applied': has_applied,
        'can_apply': request.user.is_authenticated and request.user.is_candidate() and not has_applied
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
        # Redirect to job list instead of detail to avoid any API view confusion
        return redirect('jobs:job-list')
    
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
    
    # Process applications without scores (batch processing for first 10)
    from .services import process_application
    processed_count = 0
    for app in applications[:10]:  # Process first 10 to avoid timeout
        if app.score is None:
            try:
                process_application(app)
                processed_count += 1
            except Exception as e:
                logger.warning(f"Could not process application {app.id}: {str(e)}")
    
    if processed_count > 0:
        # Refresh applications from database
        applications = list(applications)
        for i, app in enumerate(applications[:10]):
            if app.score is None:
                app.refresh_from_db()
    
    context = {'applications': applications}
    return render(request, 'jobs/application_list.html', context)


@login_required
def application_create_view(request):
    """Create a new application."""
    if not request.user.is_candidate():
        messages.error(request, 'Only candidates can apply for jobs.')
        return redirect('jobs:job-list')
    
    if request.method == 'POST':
        job_id = request.POST.get('job_id')
        resume_id = request.POST.get('resume_id')
        
        if not job_id or not resume_id:
            messages.error(request, 'Missing required fields.')
            return redirect('jobs:job-list')
        
        job = get_object_or_404(JobDescription, pk=job_id)
        resume = get_object_or_404(Resume, pk=resume_id, candidate=request.user)
        
        # Check if already applied
        if Application.objects.filter(job=job, resume=resume).exists():
            messages.warning(request, 'You have already applied for this job.')
            return redirect('jobs:job-detail', pk=job.id)
        
        # Ensure job and resume have embeddings
        if job.embedding is None:
            # Generate job embedding if missing
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
                logger.warning(f"Could not generate job embedding: {str(e)}")
        
        if resume.embedding is None:
            # Generate resume embedding if missing
            try:
                text = resume.raw_text or ' '.join(resume.skills) or ' '.join(resume.education)
                if text:
                    response = requests.post(
                        f"{settings.MATCHER_SERVICE_URL}/api/embed",
                        json={'text': text},
                        timeout=10
                    )
                    if response.status_code == 200:
                        embedding = response.json().get('embedding')
                        if embedding:
                            resume.embedding = embedding
                            resume.save(update_fields=['embedding'])
            except Exception as e:
                logger.warning(f"Could not generate resume embedding: {str(e)}")
        
        # Create application
        application = Application.objects.create(
            job=job,
            resume=resume,
            status='pending'
        )
        
        # Process application with all ML services
        from .services import process_application
        try:
            application = process_application(application)
        except Exception as e:
            logger.error(f"Error processing application: {str(e)}")
            # Continue even if processing fails
        
        messages.success(request, 'Application submitted successfully!')
        return redirect('jobs:application-detail', pk=application.id)
    
    return redirect('jobs:job-list')


@login_required
def application_update_view(request, pk):
    """Update application status (for recruiters)."""
    application = get_object_or_404(Application, pk=pk)
    
    if not request.user.is_recruiter() or application.job.posted_by != request.user:
        messages.error(request, 'Access denied.')
        return redirect('jobs:application-list')
    
    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        if status in ['pending', 'reviewing', 'shortlisted', 'rejected', 'hired']:
            application.status = status
            if notes:
                application.notes = notes
            application.save(update_fields=['status', 'notes'])
            messages.success(request, f'Application status updated to {status}.')
        else:
            messages.error(request, 'Invalid status.')
    
    return redirect('jobs:application-detail', pk=application.id)


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
    
    # Process application if score is missing (on-the-fly processing)
    if application.score is None:
        from .services import process_application
        try:
            application = process_application(application)
            # Refresh from database
            application.refresh_from_db()
        except Exception as e:
            logger.warning(f"Could not process application {application.id}: {str(e)}")
    
    context = {'application': application}
    return render(request, 'jobs/application_detail.html', context)


@login_required
def job_api_html_view(request):
    """Custom HTML view for Job API that properly handles array fields (recruiters only)."""
    if not request.user.is_recruiter():
        messages.error(request, 'Only recruiters can access the job API interface.')
        return redirect('jobs:job-list')
    
    jobs = JobDescription.objects.filter(posted_by=request.user).order_by('-created_at')
    
    # Serialize jobs for JSON display
    from .serializers import JobDescriptionSerializer
    serialized_jobs = [JobDescriptionSerializer(job).data for job in jobs]
    
    return render(request, 'jobs/job_api.html', {
        'jobs': jobs,
        'jobs_json': json.dumps(serialized_jobs),
        'api_url': '/jobs/api/jobs/'
    })

