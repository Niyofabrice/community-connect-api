from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Report
from .serializers import ReportSerializer
from attachments.services import AttachmentService
from .permissions import IsOwnerOrStaff
from django_filters.rest_framework import DjangoFilterBackend

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsOwnerOrStaff]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'category']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'status']

    def get_queryset(self):
        """
        Optimized queryset with prefetch for attachments and category
        """
        queryset = Report.objects.all().prefetch_related('attachments', 'category')
        
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'role') and user.role == 'CITIZEN':
            return queryset.filter(user=user)
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Handle multi-part file upload and trigger processing
        """
        files = request.FILES.getlist('files')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        report = serializer.save()

        # Process attachments
        for f in files:
            AttachmentService.process_upload(report, f)
        
        return Response(
            self.get_serializer(report).data, 
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'], url_path='categories')
    def get_report_categories(self, request):
        """Retrieve report categories"""
        choices = [
            {"id": key, "name": label} 
            for key, label in Report.Category.choices
        ]
        return Response(choices)

