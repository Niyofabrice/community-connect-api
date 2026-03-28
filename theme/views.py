from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from reports.models import Report, Category
from attachments.services import AttachmentService
from reports.serializers import ReportSerializer

class ReportListView(LoginRequiredMixin, ListView):
    model = Report
    template_name = 'theme/report_list.html'
    context_object_name = 'reports'
    paginate_by = 10

    def get_queryset(self):
        # Prefetching 'category' is key here to show names without extra queries
        queryset = Report.objects.all().prefetch_related('attachments', 'category')
        if self.request.user.role == 'CITIZEN':
            return queryset.filter(user=self.request.user)
        return queryset
    
class ReportDetailView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = 'theme/report_detail.html'
    context_object_name = 'report'

class ReportCreateView(LoginRequiredMixin, CreateView):
    model = Report
    fields = ['title', 'description', 'category', 'custom_category']
    template_name = 'theme/report_form.html'
    success_url = reverse_lazy('report-list')

    def form_valid(self, form):
        # 1. Prepare data for the Serializer
        data = form.cleaned_data
        files = self.request.FILES.getlist('attachment_files')

        # 2. Use your existing API Serializer for validation
        serializer = ReportSerializer(
            data=data, 
            context={'request': self.request} # Pass request for CurrentUserDefault
        )
        
        if serializer.is_valid():
            # 3. Save using the Serializer logic (This runs your create/validate methods)
            report = serializer.save()
            
            # 4. Trigger the shared Attachment Service
            for f in files:
                AttachmentService.process_upload(report, f)
                
            return super().form_valid(form)
        else:
            # If API validation fails, show errors on the Web Form
            for field, errors in serializer.errors.items():
                form.add_error(field, errors)
            return self.form_invalid(form)