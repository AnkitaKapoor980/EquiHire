from django.urls import path
from .views import health_check, api_info

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('info/', api_info, name='api_info'),
]

