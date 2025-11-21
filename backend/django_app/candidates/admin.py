from django.contrib import admin
from .models import Resume, CandidateProfile


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'file_name', 'file_type', 'is_active', 'uploaded_at')
    list_filter = ('is_active', 'file_type', 'uploaded_at')
    search_fields = ('candidate__email', 'file_name', 'skills')
    readonly_fields = ('uploaded_at', 'updated_at')
    fieldsets = (
        ('File Information', {
            'fields': ('candidate', 'file_name', 'file_path', 'file_size', 'file_type')
        }),
        ('Parsed Data', {
            'fields': ('raw_text', 'parsed_data', 'skills', 'education', 'experience_years', 'certifications')
        }),
        ('ML Data', {
            'fields': ('embedding',)
        }),
        ('Status', {
            'fields': ('is_active', 'uploaded_at', 'updated_at')
        }),
    )


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_position', 'years_of_experience', 'education_level', 'created_at')
    list_filter = ('education_level', 'created_at')
    search_fields = ('user__email', 'current_position', 'current_company')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Professional Info', {
            'fields': ('summary', 'current_position', 'current_company', 'years_of_experience', 'education_level')
        }),
        ('Preferences', {
            'fields': ('preferred_locations', 'preferred_salary_min', 'preferred_salary_max')
        }),
        ('Links', {
            'fields': ('linkedin_url', 'github_url', 'portfolio_url')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

