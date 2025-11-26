from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

urlpatterns = [
    # Health check endpoint
    path('health/', api_view(['GET'])(
        permission_classes([AllowAny])(
            lambda request: Response(
                {'status': 'healthy', 'service': 'accounts-api'},
                status=status.HTTP_200_OK
            )
        )
    ), name='health-check'),
]

# Add JWT endpoints if the package is installed
try:
    from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
    urlpatterns += [
        path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ]
except ImportError:
    pass
