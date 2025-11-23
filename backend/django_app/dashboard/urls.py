from django.urls import path
from .views import (
    recruiter_dashboard, candidate_dashboard, analytics,
    recruiter_dashboard_view, candidate_dashboard_view, analytics_view_html
)

from django.views.generic import RedirectView

app_name = 'dashboard'

urlpatterns = [
    # HTML views
    path('recruiter/', recruiter_dashboard_view, name='recruiter_dashboard'),
    path('candidate/', candidate_dashboard_view, name='candidate_dashboard'),
    path('analytics/', analytics_view_html, name='analytics'),
    # API views
    path('api/recruiter/', recruiter_dashboard, name='api_recruiter_dashboard'),
    path('api/candidate/', candidate_dashboard, name='api_candidate_dashboard'),
    path('api/analytics/', analytics, name='api_analytics'),
]

