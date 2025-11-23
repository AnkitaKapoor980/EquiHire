from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    UserRegistrationView, login_view, profile_view, update_profile_view,
    login_view_html, profile_view_html, register_view_html
)

app_name = 'accounts'

urlpatterns = [
    # HTML views
    path('login/', login_view_html, name='login'),
    path('register/', register_view_html, name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', profile_view_html, name='profile'),
    # API views
    path('api/login/', login_view, name='api_login'),
    path('api/register/', UserRegistrationView.as_view(), name='api_register'),
    path('api/profile/', profile_view, name='api_profile'),
    path('api/profile/update/', update_profile_view, name='api_update_profile'),
]

