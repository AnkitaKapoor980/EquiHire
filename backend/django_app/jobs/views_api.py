from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_list(request):
    """
    List all jobs
    """
    # TODO: Implement job listing logic
    return Response({
        'status': 'success',
        'data': [],
        'message': 'Job list endpoint'
    }, status=status.HTTP_200_OK)

# Add more API views as needed
