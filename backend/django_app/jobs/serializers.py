from rest_framework import serializers
from .models import JobDescription, Application
from accounts.serializers import UserSerializer
from candidates.serializers import ResumeSerializer


class JobDescriptionSerializer(serializers.ModelSerializer):
    """Serializer for JobDescription model."""
    posted_by = UserSerializer(read_only=True)
    application_count = serializers.SerializerMethodField()
    
    class Meta:
        model = JobDescription
        fields = (
            'id', 'title', 'description', 'requirements', 'location',
            'salary_min', 'salary_max', 'employment_type', 'required_skills',
            'posted_by', 'is_active', 'application_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'posted_by')
    
    def get_application_count(self, obj):
        return obj.applications.count()


class JobDescriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating job descriptions."""
    class Meta:
        model = JobDescription
        fields = (
            'title', 'description', 'requirements', 'location',
            'salary_min', 'salary_max', 'employment_type', 'required_skills', 'is_active'
        )
    
    def create(self, validated_data):
        validated_data['posted_by'] = self.context['request'].user
        return super().create(validated_data)


class ApplicationSerializer(serializers.ModelSerializer):
    """Serializer for Application model."""
    job = JobDescriptionSerializer(read_only=True)
    resume = ResumeSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Application
        fields = (
            'id', 'job', 'resume', 'score', 'ranking', 'fairness_metrics',
            'explanation', 'status', 'notes', 'reviewed_by', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'reviewed_by')


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating applications."""
    class Meta:
        model = Application
        fields = ('job', 'resume', 'notes')
    
    def validate(self, attrs):
        # Check if application already exists
        if Application.objects.filter(job=attrs['job'], resume=attrs['resume']).exists():
            raise serializers.ValidationError('Application already exists for this job and resume')
        return attrs


class ApplicationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating application status."""
    class Meta:
        model = Application
        fields = ('status', 'notes', 'reviewed_by')
    
    def update(self, instance, validated_data):
        if 'reviewed_by' not in validated_data:
            validated_data['reviewed_by'] = self.context['request'].user
        return super().update(instance, validated_data)

