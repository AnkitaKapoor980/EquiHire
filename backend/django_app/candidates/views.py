from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
import requests
from django.conf import settings
import logging

from .models import Resume, CandidateProfile
from .serializers import (
    ResumeSerializer,
    ResumeCreateSerializer,
    CandidateProfileSerializer
)
from .services import MinIOService

logger = logging.getLogger(__name__)


@login_required
def resume_list_view(request):
    """HTML view for resume list."""
    resumes = Resume.objects.filter(candidate=request.user).order_by('-uploaded_at')
    return render(request, 'candidates/resume_list.html', {'resumes': resumes})

@login_required
def resume_upload_view(request):
    """HTML view for resume upload."""
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, 'Please select a file.')
            return render(request, 'candidates/resume_upload.html')
        
        # Call the API endpoint logic
        from .services import MinIOService
        minio_service = MinIOService()
        
        try:
            file_path = minio_service.upload_file(file, request.user.id)
            
            # Call parser service
            file.seek(0)
            files = {'file': (file.name, file, file.content_type)}
            parser_response = requests.post(
                f"{settings.PARSER_SERVICE_URL}/api/parse",
                files=files,
                timeout=30
            )
            
            if parser_response.status_code != 200:
                minio_service.delete_file(file_path)
                messages.error(request, 'Failed to parse resume.')
                return render(request, 'candidates/resume_upload.html')
            
            parsed_data = parser_response.json()
            
            resume = Resume.objects.create(
                candidate=request.user,
                file_name=file.name,
                file_path=file_path,
                file_size=file.size,
                file_type=file.content_type,
                raw_text=parsed_data.get('raw_text', ''),
                parsed_data=parsed_data.get('parsed_data', {}),
                skills=parsed_data.get('skills', []),
                education=parsed_data.get('education', []),
                experience_years=parsed_data.get('experience_years'),
                certifications=parsed_data.get('certifications', [])
            )
            
            messages.success(request, 'Resume uploaded and parsed successfully!')
            return redirect('candidates:resume-list')
        except Exception as e:
            messages.error(request, f'Error uploading resume: {str(e)}')
            return render(request, 'candidates/resume_upload.html')
    
    return render(request, 'candidates/resume_upload.html')

class ResumeViewSet(viewsets.ModelViewSet):
    """ViewSet for Resume model."""
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own resumes
        return Resume.objects.filter(candidate=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Upload and parse a resume."""
        serializer = ResumeCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        file = serializer.validated_data['file']
        minio_service = MinIOService()
        
        try:
            # Upload file to MinIO
            file_path = minio_service.upload_file(file, request.user.id)
            
            # Call parser service
            file.seek(0)  # Reset file pointer
            files = {'file': (file.name, file, file.content_type)}
            
            parser_response = requests.post(
                f"{settings.PARSER_SERVICE_URL}/api/parse",
                files=files,
                timeout=30
            )
            
            if parser_response.status_code != 200:
                # Delete uploaded file if parsing fails
                minio_service.delete_file(file_path)
                return Response(
                    {'error': 'Failed to parse resume'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            parsed_data = parser_response.json()
            
            # Create Resume object
            resume = Resume.objects.create(
                candidate=request.user,
                file_name=file.name,
                file_path=file_path,
                file_size=file.size,
                file_type=file.content_type,
                raw_text=parsed_data.get('raw_text', ''),
                parsed_data=parsed_data.get('parsed_data', {}),
                skills=parsed_data.get('skills', []),
                education=parsed_data.get('education', []),
                experience_years=parsed_data.get('experience_years'),
                certifications=parsed_data.get('certifications', [])
            )
            
            # Generate embedding
            try:
                self._generate_embedding(resume)
            except Exception as e:
                logger.error(f"Failed to generate embedding for resume {resume.id}: {str(e)}")
            
            return Response(
                ResumeSerializer(resume).data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Error uploading resume: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_embedding(self, resume):
        """Generate embedding for resume using matcher service."""
        text = resume.raw_text or f"{' '.join(resume.skills)} {' '.join(resume.education)}"
        if not text:
            return
        
        try:
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
            logger.error(f"Error calling matcher service: {str(e)}")
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Get presigned URL for resume download."""
        resume = self.get_object()
        minio_service = MinIOService()
        try:
            url = minio_service.get_file_url(resume.file_path)
            return Response({'download_url': url}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error generating download URL: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CandidateProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for CandidateProfile model."""
    queryset = CandidateProfile.objects.all()
    serializer_class = CandidateProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own profile
        return CandidateProfile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_object(self):
        # Get or create profile
        profile, created = CandidateProfile.objects.get_or_create(
            user=self.request.user
        )
        return profile

