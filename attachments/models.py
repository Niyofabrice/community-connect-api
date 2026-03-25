from django.db import models

def get_upload_path(instance, filename):
    # This organizing files to prevent filename collisions
    # e.g., uploads/a1/b2/a1b2c3d4...jpg
    return f"uploads/{instance.sha256_hash[:2]}/{instance.sha256_hash[2:4]}/{instance.sha256_hash}"

class Attachment(models.Model):
    class ProcessingStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Scan'
        SCANNING = 'SCANNING', 'Scanning/Processing'
        CLEAN = 'CLEAN', 'Clean'
        MALICIOUS = 'MALICIOUS', 'Malicious - Quarantined'
        ERROR = "ERROR", "Processing Error"

    report = models.ForeignKey('reports.Report', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=get_upload_path)
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveBigIntegerField()
    
    # Technical Metadata
    sha256_hash = models.CharField(max_length=64, db_index=True) # For deduplication
    phash = models.CharField(max_length=64, db_index=True, null=True) # For near-duplicates
    mime_type = models.CharField(max_length=100)
    
    # Status
    processing_status = models.CharField(max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.PENDING)
    # OCR results
    extracted_text = models.TextField(blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['report', 'processing_status']),
            models.Index(fields=['sha256_hash']), 
        ]
    def __str__(self):
        return f"{self.file_name}({self.processing_status})"