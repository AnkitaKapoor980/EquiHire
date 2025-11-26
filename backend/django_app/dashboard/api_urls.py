from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

app_name = 'dashboard_api'

@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_stats(request):
    """
    Get dashboard statistics
    """
    # TODO: Implement actual dashboard statistics
    return Response({
        'status': 'success',
        'data': {
            'total_jobs': 0,
            'total_candidates': 0,
            'total_hires': 0,
            'total_pending': 0,
        },
        'message': 'Dashboard statistics endpoint'
    }, status=status.HTTP_200_OK)

urlpatterns = [
    path('stats/', dashboard_stats, name='dashboard-stats'),
    # Add more dashboard API endpoints here
]
