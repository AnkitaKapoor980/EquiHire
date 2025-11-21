from rest_framework import serializers
from .models import Resume, CandidateProfile
from accounts.serializers import UserSerializer


class ResumeSerializer(serializers.ModelSerializer):
    """Serializer for Resume model."""
    candidate = UserSerializer(read_only=True)
    
    class Meta:
        model = Resume
        fields = (
            'id', 'candidate', 'file_name', 'file_path', 'file_size', 'file_type',
            'parsed_data', 'raw_text', 'skills', 'education', 'experience_years',
            'certifications', 'is_active', 'uploaded_at', 'updated_at'
        )
        read_only_fields = ('id', 'candidate', 'uploaded_at', 'updated_at', 'file_path')


class ResumeCreateSerializer(serializers.Serializer):
    """Serializer for resume upload."""
    file = serializers.FileField(required=True)
    
    def validate_file(self, value):
        # Validate file type
        allowed_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError('Only PDF and DOCX files are allowed')
        
        # Validate file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError('File size cannot exceed 10MB')
        
        return value


class CandidateProfileSerializer(serializers.ModelSerializer):
    """Serializer for CandidateProfile model."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = CandidateProfile
        fields = (
            'id', 'user', 'summary', 'current_position', 'current_company',
            'years_of_experience', 'education_level', 'preferred_locations',
            'preferred_salary_min', 'preferred_salary_max', 'linkedin_url',
            'github_url', 'portfolio_url', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

