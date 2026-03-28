import clamd
import pytesseract
import tempfile
import os
from PIL import Image
from pdf2image import convert_from_path
from celery import shared_task
from django.core.files.storage import default_storage
from .models import Attachment
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings

def quarantine_file(attachment):
    """
    Physically moves the file from its current location to a restricted 
    quarantine folder and updates the file path in the database.
    """
    old_path = attachment.file.name
    filename = os.path.basename(old_path)
    new_path = os.path.join(settings.QUARANTINE_ROOT, filename)

    # 1. Read the content from the current location
    with attachment.file.open('rb') as f:
        file_content = f.read()

    # 2. Save it to the new "Quarantine" location
    # Use ContentFile to wrap the raw bytes
    new_file_name = default_storage.save(new_path, ContentFile(file_content))

    # 3. Update the attachment record to point to the new path
    attachment.file.name = new_file_name
    attachment.save(update_fields=['file'])

    # 4. Delete the original "public" file
    if default_storage.exists(old_path):
        default_storage.delete(old_path)


@shared_task(bind=True, max_retries=3)
def process_attachment_pipeline(self, attachment_id):
    try:
        attachment = Attachment.objects.get(id=attachment_id)
    except Attachment.DoesNotExist:
        return f"Attachment {attachment_id} not found."

    attachment.processing_status = Attachment.ProcessingStatus.SCANNING
    attachment.save(update_fields=['processing_status'])

    try:
        # 1. Virus scan using stream (memory efficient)
        cd = clamd.ClamdNetworkSocket(host='clamav', port=3310)
        with attachment.file.open('rb') as f:
            scan_result = cd.instream(f)

        if scan_result and scan_result['stream'][0] == 'FOUND':
            attachment.processing_status = Attachment.ProcessingStatus.MALICIOUS
            attachment.save(update_fields=['processing_status'])
            return f"Virus found in {attachment_id}"

        # 2. OCR Processing
        # Use a temporary file to ensure pytesseract/pdf2image can read it
        # regardless of where the file is stored (Local, S3, etc.)
        extracted_text = ""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            with attachment.file.open('rb') as f:
                tmp_file.write(f.read())
            tmp_path = tmp_file.name

        try:
            if 'image' in attachment.mime_type:
                with Image.open(tmp_path) as img:
                    extracted_text = pytesseract.image_to_string(img)

            elif 'pdf' in attachment.mime_type:
                images = convert_from_path(tmp_path)
                for img in images:
                    extracted_text += pytesseract.image_to_string(img) + "\n"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        attachment.extracted_text = extracted_text
        attachment.processing_status = Attachment.ProcessingStatus.CLEAN
        attachment.save(update_fields=['extracted_text', 'processing_status'])

    except Exception as exc:
        attachment.processing_status = Attachment.ProcessingStatus.ERROR
        attachment.save(update_fields=['processing_status'])
        raise self.retry(exc=exc, countdown=60)

    return f"Attachment {attachment_id} processed successfully."