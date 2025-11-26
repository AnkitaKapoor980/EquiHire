import platform
import sys
from datetime import datetime
from django.db import connection
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Comprehensive health check endpoint."""
    # Basic health status
    status_code = status.HTTP_200_OK
    data = {
        'status': 'healthy',
        'service': 'equihire-api',
        'timestamp': datetime.utcnow().isoformat(),
        'version': getattr(settings, 'VERSION', '0.1.0'),
        'environment': getattr(settings, 'ENVIRONMENT', 'development'),
        'python_version': platform.python_version(),
        'django_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'database': {
            'default': 'connected' if connection.ensure_connection() is None else 'disconnected'
        },
        'services': {}
    }

    # Check external services if needed
    # Example: Check Redis, Celery, etc.
    
    return Response(data, status=status_code)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request):
    """API information endpoint."""
    return Response({
        'name': 'EquiHire API',
        'version': '1.0.0',
        'description': 'Applicant Tracking System with AI-powered Resume Screening',
        'endpoints': {
            'auth': '/api/auth/',
            'jobs': '/api/jobs/',
            'candidates': '/api/candidates/',
            'dashboard': '/api/dashboard/',
        }
    }, status=status.HTTP_200_OK)

