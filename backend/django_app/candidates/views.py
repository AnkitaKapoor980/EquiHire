from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse
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
def resume_api_html_view(request):
    """Custom HTML view for Resume API that properly handles array fields."""
    resumes = Resume.objects.filter(candidate=request.user).order_by('-uploaded_at')
    
    # Serialize resumes for JSON display
    from .serializers import ResumeSerializer
    import json
    serialized_resumes = [ResumeSerializer(resume).data for resume in resumes]
    
    return render(request, 'candidates/resume_api.html', {
        'resumes': resumes,
        'resumes_json': json.dumps(serialized_resumes),
        'api_url': '/candidates/api/resumes/'
    })

@login_required
def resume_download_view(request, resume_id):
    """Download a resume file from MinIO."""
    try:
        resume = Resume.objects.get(id=resume_id, candidate=request.user)
        
        # Get file from MinIO
        minio_service = MinIOService()
        file_obj = minio_service.get_file(resume.file_path)
        
        # Create streaming response
        response = StreamingHttpResponse(
            file_obj,
            content_type=resume.file_type
        )
        response['Content-Disposition'] = f'attachment; filename="{resume.file_name}"'
        response['Content-Length'] = resume.file_size
        
        return response
    except Resume.DoesNotExist:
        messages.error(request, 'Resume not found or you do not have permission to access it.')
        return redirect('candidates:resume-list')
    except Exception as e:
        logger.error(f"Error downloading resume: {str(e)}")
        messages.error(request, f'Error downloading resume: {str(e)}')
        return redirect('candidates:resume-list')

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
            
            # Try to call parser service, but allow upload without parsing if service is unavailable
            parsed_data = {}
            try:
                file.seek(0)
                files = {'file': (file.name, file, file.content_type)}
                parser_response = requests.post(
                    f"{settings.PARSER_SERVICE_URL}/api/parse",
                    files=files,
                    timeout=10
                )
                
                if parser_response.status_code == 200:
                    parsed_data = parser_response.json()
                    logger.info(f"Resume parsed successfully for {file.name}")
                else:
                    logger.warning(f"Parser service returned {parser_response.status_code}, continuing without parsing")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Parser service unavailable: {str(e)}. Uploading resume without parsing.")
                # Continue without parsing - file is already uploaded to MinIO
            
            # Extract basic text from file if parsing failed
            raw_text = parsed_data.get('raw_text', '')
            if not raw_text and file.content_type == 'application/pdf':
                try:
                    import fitz  # PyMuPDF
                    file.seek(0)
                    doc = fitz.open(stream=file.read(), filetype='pdf')
                    raw_text = '\n'.join([page.get_text() for page in doc])
                    doc.close()
                except Exception as e:
                    logger.warning(f"Could not extract text from PDF: {str(e)}")
            
            resume = Resume.objects.create(
                candidate=request.user,
                file_name=file.name,
                file_path=file_path,
                file_size=file.size,
                file_type=file.content_type,
                raw_text=raw_text,
                parsed_data=parsed_data.get('parsed_data', {}),
                skills=parsed_data.get('skills', []),
                education=parsed_data.get('education', []),
                experience_years=parsed_data.get('experience_years'),
                certifications=parsed_data.get('certifications', [])
            )
            
            if parsed_data:
                messages.success(request, 'Resume uploaded and parsed successfully!')
            else:
                messages.success(request, 'Resume uploaded successfully! (Parsing will be done later)')
            return redirect('candidates:resume-list')
        except Exception as e:
            logger.error(f"Error uploading resume: {str(e)}")
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
        if self.request.user.is_authenticated:
            return Resume.objects.filter(candidate=self.request.user)
        return Resume.objects.none()
    
    def _is_browser_request(self, request):
        """Check if request is from a browser."""
        accept_header = request.META.get('HTTP_ACCEPT', '')
        return 'text/html' in accept_header or (
            hasattr(request, 'accepted_renderer') and 
            request.accepted_renderer.format == 'html'
        )
    
    def list(self, request, *args, **kwargs):
        """List resumes. Redirect browser requests to HTML view."""
        if self._is_browser_request(request):
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect('/candidates/resumes/')
        return super().list(request, *args, **kwargs)
    
    def retrieve(self, request, *args, **kwargs):
        """Get resume detail. Redirect browser requests to HTML view."""
        if self._is_browser_request(request):
            from django.http import HttpResponseRedirect
            pk = kwargs.get('pk')
            return HttpResponseRedirect(f'/candidates/resumes/')
        return super().retrieve(request, *args, **kwargs)
    
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
            
            # Try to call parser service, but allow upload without parsing if service is unavailable
            parsed_data = {}
            try:
                file.seek(0)  # Reset file pointer
                files = {'file': (file.name, file, file.content_type)}
                
                parser_response = requests.post(
                    f"{settings.PARSER_SERVICE_URL}/api/parse",
                    files=files,
                    timeout=10
                )
                
                if parser_response.status_code == 200:
                    parsed_data = parser_response.json()
                    logger.info(f"Resume parsed successfully for {file.name}")
                else:
                    logger.warning(f"Parser service returned {parser_response.status_code}, continuing without parsing")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Parser service unavailable: {str(e)}. Uploading resume without parsing.")
                # Continue without parsing - file is already uploaded to MinIO
            
            # Extract basic text from file if parsing failed
            raw_text = parsed_data.get('raw_text', '')
            if not raw_text and file.content_type == 'application/pdf':
                try:
                    import fitz  # PyMuPDF
                    file.seek(0)
                    doc = fitz.open(stream=file.read(), filetype='pdf')
                    raw_text = '\n'.join([page.get_text() for page in doc])
                    doc.close()
                except Exception as e:
                    logger.warning(f"Could not extract text from PDF: {str(e)}")
            
            # Create Resume object
            resume = Resume.objects.create(
                candidate=request.user,
                file_name=file.name,
                file_path=file_path,
                file_size=file.size,
                file_type=file.content_type,
                raw_text=raw_text,
                parsed_data=parsed_data.get('parsed_data', {}),
                skills=parsed_data.get('skills', []),
                education=parsed_data.get('education', []),
                experience_years=parsed_data.get('experience_years'),
                certifications=parsed_data.get('certifications', [])
            )
            
            # Generate embedding (optional, can fail gracefully)
            try:
                self._generate_embedding(resume)
            except Exception as e:
                logger.warning(f"Failed to generate embedding for resume {resume.id}: {str(e)}")
            
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

