from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

# Import views_api if it exists
try:
    from . import views_api
    urlpatterns = [
        path('', views_api.job_list, name='job-list'),
        # Add more job-related API endpoints here
    ]
except ImportError:
    # Fallback if views_api doesn't exist
    @api_view(['GET'])
    @permission_classes([AllowAny])
    def not_implemented(request):
        return Response({
            'status': 'success',
            'message': 'This endpoint is not implemented yet',
            'endpoint': request.path
        }, status=status.HTTP_501_NOT_IMPLEMENTED)
    
    urlpatterns = [
        path('', not_implemented, name='job-list'),
    ]

app_name = 'jobs_api'
