from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .models import JobDescription, Application
from .serializers import (
    JobDescriptionSerializer,
    JobDescriptionCreateSerializer,
    ApplicationSerializer,
    ApplicationCreateSerializer,
    ApplicationUpdateSerializer
)
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class JobDescriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for JobDescription model."""
    queryset = JobDescription.objects.filter(is_active=True)
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employment_type', 'location', 'posted_by']
    search_fields = ['title', 'description', 'requirements']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return JobDescriptionCreateSerializer
        return JobDescriptionSerializer
    
    def get_queryset(self):
        """Filter queryset based on user role."""
        queryset = super().get_queryset()
        # Recruiters see all active jobs, candidates see all active jobs (read-only)
        return queryset
    
    def _is_browser_request(self, request):
        """Check if request is from a browser."""
        accept_header = request.META.get('HTTP_ACCEPT', '')
        return 'text/html' in accept_header or (
            hasattr(request, 'accepted_renderer') and 
            request.accepted_renderer.format == 'html'
        )
    
    def list(self, request, *args, **kwargs):
        """List jobs. Redirect all browser requests to HTML view."""
        if self._is_browser_request(request):
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect('/jobs/')
        return super().list(request, *args, **kwargs)
    
    def retrieve(self, request, *args, **kwargs):
        """Get job detail. Redirect browser requests to HTML view."""
        if self._is_browser_request(request):
            from django.http import HttpResponseRedirect
            pk = kwargs.get('pk')
            return HttpResponseRedirect(f'/jobs/{pk}/')
        return super().retrieve(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """Create job. Only recruiters can create."""
        if not request.user.is_recruiter():
            return Response(
                {'error': 'Only recruiters can create job postings.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Update job. Only the job poster can update."""
        job = self.get_object()
        if not request.user.is_recruiter() or job.posted_by != request.user:
            return Response(
                {'error': 'You can only update your own job postings.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete job. Only the job poster can delete."""
        job = self.get_object()
        if not request.user.is_recruiter() or job.posted_by != request.user:
            return Response(
                {'error': 'You can only delete your own job postings.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        job = serializer.save()
        # Generate embedding for the job description
        try:
            self._generate_embedding(job)
        except Exception as e:
            logger.error(f"Failed to generate embedding for job {job.id}: {str(e)}")
    
    def _generate_embedding(self, job):
        """Generate embedding for job description using matcher service."""
        text = f"{job.title} {job.description} {job.requirements}"
        try:
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
            logger.error(f"Error calling matcher service: {str(e)}")
    
    @action(detail=True, methods=['post'])
    def match_candidates(self, request, pk=None):
        """Match candidates for a specific job."""
        job = self.get_object()
        if job.embedding is None:
            return Response(
                {'error': 'Job embedding not available. Please wait for embedding generation.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Call matcher service to find top candidates
        try:
            response = requests.post(
                f"{settings.MATCHER_SERVICE_URL}/api/match",
                json={
                    'job_embedding': job.embedding,
                    'job_id': job.id,
                    'top_k': request.data.get('top_k', 10)
                },
                timeout=30
            )
            if response.status_code == 200:
                matches = response.json().get('matches', [])
                return Response({'matches': matches}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Failed to match candidates'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(f"Error matching candidates: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for Application model."""
    queryset = Application.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['job', 'status', 'resume']
    ordering_fields = ['score', 'created_at']
    ordering = ['-score', '-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ApplicationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ApplicationUpdateSerializer
        return ApplicationSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_recruiter():
            # Recruiters see applications for their jobs
            return Application.objects.filter(job__posted_by=user)
        elif user.is_candidate():
            # Candidates see their own applications
            return Application.objects.filter(resume__candidate=user)
        return Application.objects.none()
    
    def _is_browser_request(self, request):
        """Check if request is from a browser."""
        accept_header = request.META.get('HTTP_ACCEPT', '')
        return 'text/html' in accept_header or (
            hasattr(request, 'accepted_renderer') and 
            request.accepted_renderer.format == 'html'
        )
    
    def list(self, request, *args, **kwargs):
        """List applications. Redirect all browser requests to HTML view."""
        if self._is_browser_request(request):
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect('/jobs/applications/')
        return super().list(request, *args, **kwargs)
    
    def retrieve(self, request, *args, **kwargs):
        """Get application detail. Redirect browser requests to HTML view."""
        if self._is_browser_request(request):
            from django.http import HttpResponseRedirect
            pk = kwargs.get('pk')
            return HttpResponseRedirect(f'/jobs/applications/{pk}/')
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def audit_fairness(self, request, pk=None):
        """Audit application for fairness metrics."""
        application = self.get_object()
        
        try:
            response = requests.post(
                f"{settings.FAIRNESS_SERVICE_URL}/api/audit",
                json={
                    'application_id': application.id,
                    'job_id': application.job.id,
                    'resume_id': application.resume.id,
                    'score': application.score
                },
                timeout=10
            )
            if response.status_code == 200:
                fairness_metrics = response.json().get('metrics', {})
                application.fairness_metrics = fairness_metrics
                application.save(update_fields=['fairness_metrics'])
                return Response({'metrics': fairness_metrics}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Failed to audit fairness'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(f"Error auditing fairness: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def explain(self, request, pk=None):
        """Get SHAP explanation for application."""
        application = self.get_object()
        
        try:
            response = requests.post(
                f"{settings.EXPLAINABILITY_SERVICE_URL}/api/explain",
                json={
                    'application_id': application.id,
                    'job_id': application.job.id,
                    'resume_id': application.resume.id,
                    'score': application.score
                },
                timeout=10
            )
            if response.status_code == 200:
                explanation = response.json().get('explanation', {})
                application.explanation = explanation
                application.save(update_fields=['explanation'])
                return Response({'explanation': explanation}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Failed to generate explanation'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

