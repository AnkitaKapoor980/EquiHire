from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResumeViewSet, CandidateProfileViewSet, resume_list_view, resume_upload_view, resume_api_html_view

app_name = 'candidates'

router = DefaultRouter()
router.register(r'resumes', ResumeViewSet, basename='resume')
router.register(r'profiles', CandidateProfileViewSet, basename='profile')

urlpatterns = [
    # HTML views
    path('resumes/', resume_list_view, name='resume-list'),
    path('resumes/upload/', resume_upload_view, name='resume-upload'),
    path('resumes/<int:pk>/download/', ResumeViewSet.as_view({'get': 'download'}), name='resume-download'),
    # Custom HTML view for API (handles array fields properly)
    path('api/resumes/html/', resume_api_html_view, name='resume-api-html'),
    # API views
    path('api/', include(router.urls)),
]

