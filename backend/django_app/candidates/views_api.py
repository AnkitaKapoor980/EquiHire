from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def candidate_list(request):
    """
    List all candidates
    """
    # TODO: Implement candidate listing logic
    return Response({
        'status': 'success',
        'data': [],
        'message': 'Candidate list endpoint'
    }, status=status.HTTP_200_OK)

# Add more API views as needed
