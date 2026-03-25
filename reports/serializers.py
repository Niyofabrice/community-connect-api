from rest_framework import serializers
from .models import Report, Category
from attachments.models import Attachment

class AttachmentSerializer(serializers.ModelSerializer):
    """
    Shows the status of the 'Security-first' pipeline to the frontend.
    """
    class Meta:
        model = Attachment
        fields = [
            'id', 'file', 'file_name', 'mime_type', 
            'processing_status', 'extracted_text', 'created_at'
        ]
        read_only_fields = fields

class ReportSerializer(serializers.ModelSerializer):
    # Nested serializer to show all files related to this report
    attachments = AttachmentSerializer(many=True, read_only=True)
    # Human-readable labels for the Status choices
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    # Link to the username instead of just an ID
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'title', 'description', 'category', 'status', 
            'status_display', 'user_name', 'attachments', 'created_at'
        ]
        read_only_fields = ['status', 'user']

    def create(self, validated_data):
        # Automatically assign the report to the logged-in user
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)