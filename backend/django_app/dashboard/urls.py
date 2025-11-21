from django.urls import path
from .views import (
    recruiter_dashboard, candidate_dashboard, analytics,
    recruiter_dashboard_view, candidate_dashboard_view
)

from django.views.generic import RedirectView

urlpatterns = [
    # Home redirect
    path('', RedirectView.as_view(pattern_name='dashboard:recruiter_dashboard', permanent=False), name='home'),
    # HTML views
    path('recruiter/', recruiter_dashboard_view, name='recruiter_dashboard'),
    path('candidate/', candidate_dashboard_view, name='candidate_dashboard'),
    # API views
    path('api/recruiter/', recruiter_dashboard, name='api_recruiter_dashboard'),
    path('api/candidate/', candidate_dashboard, name='api_candidate_dashboard'),
    path('api/analytics/', analytics, name='analytics'),
]

