from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from jobs.models import JobDescription, Application
from candidates.models import Resume
from accounts.models import User
import logging

logger = logging.getLogger(__name__)


@login_required
def recruiter_dashboard_view(request):
    """HTML view for recruiter dashboard."""
    if not request.user.is_recruiter():
        return render(request, 'base/base.html', {'error': 'Access denied'})
    
    user = request.user
    total_jobs = JobDescription.objects.filter(posted_by=user).count()
    active_jobs = JobDescription.objects.filter(posted_by=user, is_active=True).count()
    total_applications = Application.objects.filter(job__posted_by=user).count()
    pending_applications = Application.objects.filter(job__posted_by=user, status='pending').count()
    shortlisted_applications = Application.objects.filter(job__posted_by=user, status='shortlisted').count()
    
    recent_applications = Application.objects.filter(
        job__posted_by=user
    ).select_related('job', 'resume', 'resume__candidate').order_by('-created_at')[:10]
    
    top_jobs = JobDescription.objects.filter(
        posted_by=user
    ).annotate(
        application_count=Count('applications')
    ).order_by('-application_count')[:5]
    
    context = {
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'shortlisted_applications': shortlisted_applications,
        'recent_applications': recent_applications,
        'top_jobs': top_jobs,
    }
    return render(request, 'dashboard/recruiter_dashboard.html', context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recruiter_dashboard(request):
    """Dashboard data for recruiters."""
    if not request.user.is_recruiter():
        return Response({'error': 'Access denied'}, status=403)
    
    user = request.user
    
    # Job statistics
    total_jobs = JobDescription.objects.filter(posted_by=user).count()
    active_jobs = JobDescription.objects.filter(posted_by=user, is_active=True).count()
    
    # Application statistics
    total_applications = Application.objects.filter(job__posted_by=user).count()
    pending_applications = Application.objects.filter(job__posted_by=user, status='pending').count()
    shortlisted_applications = Application.objects.filter(job__posted_by=user, status='shortlisted').count()
    
    # Recent applications
    recent_applications = Application.objects.filter(
        job__posted_by=user
    ).select_related('job', 'resume', 'resume__candidate').order_by('-created_at')[:10]
    
    from jobs.serializers import ApplicationSerializer
    recent_applications_data = ApplicationSerializer(recent_applications, many=True).data
    
    # Top jobs by application count
    top_jobs = JobDescription.objects.filter(
        posted_by=user
    ).annotate(
        application_count=Count('applications')
    ).order_by('-application_count')[:5]
    
    from jobs.serializers import JobDescriptionSerializer
    top_jobs_data = JobDescriptionSerializer(top_jobs, many=True).data
    
    # Average score by job
    avg_scores = Application.objects.filter(
        job__posted_by=user,
        score__isnull=False
    ).values('job__title').annotate(
        avg_score=Avg('score')
    ).order_by('-avg_score')[:5]
    
    return Response({
        'summary': {
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'total_applications': total_applications,
            'pending_applications': pending_applications,
            'shortlisted_applications': shortlisted_applications,
        },
        'recent_applications': recent_applications_data,
        'top_jobs': top_jobs_data,
        'average_scores': list(avg_scores),
    })


@login_required
def candidate_dashboard_view(request):
    """HTML view for candidate dashboard."""
    if not request.user.is_candidate():
        return render(request, 'base/base.html', {'error': 'Access denied'})
    
    user = request.user
    total_resumes = Resume.objects.filter(candidate=user).count()
    active_resumes = Resume.objects.filter(candidate=user, is_active=True).count()
    total_applications = Application.objects.filter(resume__candidate=user).count()
    pending_applications = Application.objects.filter(resume__candidate=user, status='pending').count()
    shortlisted_applications = Application.objects.filter(resume__candidate=user, status='shortlisted').count()
    rejected_applications = Application.objects.filter(resume__candidate=user, status='rejected').count()
    
    recent_applications = Application.objects.filter(
        resume__candidate=user
    ).select_related('job', 'resume').order_by('-created_at')[:10]
    
    context = {
        'total_resumes': total_resumes,
        'active_resumes': active_resumes,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'shortlisted_applications': shortlisted_applications,
        'rejected_applications': rejected_applications,
        'recent_applications': recent_applications,
    }
    return render(request, 'dashboard/candidate_dashboard.html', context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def candidate_dashboard(request):
    """Dashboard data for candidates."""
    if not request.user.is_candidate():
        return Response({'error': 'Access denied'}, status=403)
    
    user = request.user
    
    # Resume statistics
    total_resumes = Resume.objects.filter(candidate=user).count()
    active_resumes = Resume.objects.filter(candidate=user, is_active=True).count()
    
    # Application statistics
    total_applications = Application.objects.filter(resume__candidate=user).count()
    pending_applications = Application.objects.filter(resume__candidate=user, status='pending').count()
    shortlisted_applications = Application.objects.filter(resume__candidate=user, status='shortlisted').count()
    rejected_applications = Application.objects.filter(resume__candidate=user, status='rejected').count()
    
    # Recent applications
    recent_applications = Application.objects.filter(
        resume__candidate=user
    ).select_related('job', 'resume').order_by('-created_at')[:10]
    
    from jobs.serializers import ApplicationSerializer
    recent_applications_data = ApplicationSerializer(recent_applications, many=True).data
    
    # Application status distribution
    status_distribution = Application.objects.filter(
        resume__candidate=user
    ).values('status').annotate(count=Count('id'))
    
    return Response({
        'summary': {
            'total_resumes': total_resumes,
            'active_resumes': active_resumes,
            'total_applications': total_applications,
            'pending_applications': pending_applications,
            'shortlisted_applications': shortlisted_applications,
            'rejected_applications': rejected_applications,
        },
        'recent_applications': recent_applications_data,
        'status_distribution': list(status_distribution),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics(request):
    """Analytics data for recruiters."""
    if not request.user.is_recruiter():
        return Response({'error': 'Access denied'}, status=403)
    
    user = request.user
    
    # Applications over time (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    applications_over_time = Application.objects.filter(
        job__posted_by=user,
        created_at__gte=thirty_days_ago
    ).extra(
        select={'day': "date(created_at)"}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # Status distribution
    status_distribution = Application.objects.filter(
        job__posted_by=user
    ).values('status').annotate(count=Count('id'))
    
    # Top skills in applications
    from django.db.models import Q
    top_skills = Resume.objects.filter(
        applications__job__posted_by=user
    ).values('skills').annotate(
        count=Count('id', distinct=True)
    ).order_by('-count')[:10]
    
    return Response({
        'applications_over_time': list(applications_over_time),
        'status_distribution': list(status_distribution),
        'top_skills': list(top_skills),
    })

