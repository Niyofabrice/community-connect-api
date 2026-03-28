from rest_framework import serializers
from .models import Report, Category
from attachments.models import Attachment

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = [
            'id', 'file', 'file_name', 'mime_type', 
            'processing_status', 'extracted_text', 'created_at'
        ]
        read_only_fields = fields

        def to_representation(self, instance):
            """Hide the file URL if it's not CLEAN"""
            data = super().to_representation(instance)
            if instance.processing_status != Attachment.ProcessingStatus.CLEAN:
                data['file'] = None
            return data

class ReportSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    attachments = AttachmentSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'title', 'description', 'category', 'status', 
            'status_display', 'user', 'user_name', 'attachments', 'created_at'
        ]
        read_only_fields = ['created_at']

    def validate_status(self, value):
        """Only Staff/Admin can change the status"""
        user = self.context['request'].user
        if self.instance:
            if user.role == 'CITIZEN' and value != self.instance.status:
                raise serializers.ValidationError("Citizens cannot change the status of a report.")
        return value
    
    def validate(self, data):
        category = data.get('category')
        custom_category = data.get('custom_category')

        if category and category.name.lower() == "other":
            if not custom_category:
                raise serializers.ValidationError({
                    "custom_category": "Please specify your category since you selected 'Other'."
                })
        return data