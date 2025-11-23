from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobDescriptionViewSet, ApplicationViewSet
from .views_html import (
    job_list_view, job_detail_view, job_create_view,
    application_list_view, application_detail_view,
    application_create_view, application_update_view,
    job_api_html_view
)

app_name = 'jobs'

router = DefaultRouter()
router.register(r'jobs', JobDescriptionViewSet, basename='job')
router.register(r'applications', ApplicationViewSet, basename='application')

urlpatterns = [
    # HTML views
    path('', job_list_view, name='job-list'),
    path('create/', job_create_view, name='job-create'),
    path('<int:pk>/', job_detail_view, name='job-detail'),
    path('applications/', application_list_view, name='application-list'),
    path('applications/create/', application_create_view, name='application-create'),
    path('applications/<int:pk>/', application_detail_view, name='application-detail'),
    path('applications/<int:pk>/update/', application_update_view, name='application-update'),
    # Custom HTML view for API (recruiters only)
    path('api/jobs/html/', job_api_html_view, name='job-api-html'),
    # API views
    path('api/', include(router.urls)),
]

