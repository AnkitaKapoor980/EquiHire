"""
URL configuration for equihire project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

# API URL patterns
api_patterns = [
    # Core API endpoints
    path('', include('api.urls')),  # /api/
    
    # Auth endpoints (JWT)
    path('auth/', include('accounts.api_urls')),  # /api/auth/
    
    # App-specific API endpoints
    path('jobs/', include('jobs.api_urls')),  # /api/jobs/
    path('candidates/', include('candidates.api_urls')),  # /api/candidates/
    path('dashboard/', include('dashboard.api_urls')),  # /api/dashboard/
]

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Homepage
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    
    # API endpoints
    path('api/', include((api_patterns, 'api'), namespace='api')),
    
    # HTML views with namespaces
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('jobs/', include(('jobs.urls', 'jobs'), namespace='jobs')),
    path('candidates/', include(('candidates.urls', 'candidates'), namespace='candidates')),
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
