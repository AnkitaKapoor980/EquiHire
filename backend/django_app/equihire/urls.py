"""
URL configuration for equihire project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.views.generic import RedirectView
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    # HTML views with namespaces
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('jobs/', include(('jobs.urls', 'jobs'), namespace='jobs')),
    path('candidates/', include(('candidates.urls', 'candidates'), namespace='candidates')),
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
    # API views (no namespaces to avoid conflicts)
    path('api/auth/', include('accounts.urls')),
    path('api/jobs/', include('jobs.urls')),
    path('api/candidates/', include('candidates.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

