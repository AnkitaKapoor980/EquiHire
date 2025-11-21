from django.contrib import admin
from .models import JobDescription, Application


@admin.register(JobDescription)
class JobDescriptionAdmin(admin.ModelAdmin):
    list_display = ('title', 'posted_by', 'employment_type', 'is_active', 'created_at')
    list_filter = ('is_active', 'employment_type', 'created_at')
    search_fields = ('title', 'description', 'requirements')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'requirements', 'posted_by')
        }),
        ('Details', {
            'fields': ('location', 'employment_type', 'salary_min', 'salary_max', 'required_skills')
        }),
        ('ML Data', {
            'fields': ('embedding',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'resume', 'score', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('job__title', 'resume__candidate__email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Application', {
            'fields': ('job', 'resume', 'status', 'reviewed_by')
        }),
        ('ML Results', {
            'fields': ('score', 'ranking', 'fairness_metrics', 'explanation')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

