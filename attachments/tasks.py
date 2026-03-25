import clamd
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from celery import shared_task
from django.core.files.storage import default_storage
from .models import Attachment


@shared_task(bind=True, max_retries=3)
def process_attachment_pipeline(self, attachment_id):
    try:
        attachment = Attachment.objects.get(id=attachment_id)
    except Attachment.DoesNotExist:
        return f"Attachment {attachment_id} not found."

    attachment.processing_status = Attachment.ProcessingStatus.SCANNING
    attachment.save()

    try:
        # Virus scan
        cd = clamd.ClamdNetworkSocket(host='clamav', port=3310)
        
        with attachment.file.open('rb') as f:
            scan_result = cd.instream(f)

        if scan_result['stream'][0] == 'FOUND':
            attachment.processing_status = Attachment.ProcessingStatus.MALICIOUS
            attachment.save()
            # attachment.file.delete()
            return f"Virus found in {attachment_id}"

        extracted_text = ""

        # OCR Processing
        file_path = attachment.file.path  # important for pdf2image

        if 'image' in attachment.mime_type:
            with Image.open(file_path) as img:
                extracted_text = pytesseract.image_to_string(img)

        elif 'pdf' in attachment.mime_type:
            images = convert_from_path(file_path)

            for img in images:
                extracted_text += pytesseract.image_to_string(img) + "\n"

        attachment.extracted_text = extracted_text

        # Finalize
        attachment.processing_status = Attachment.ProcessingStatus.CLEAN
        attachment.save()

    except Exception as exc:
        attachment.processing_status = Attachment.ProcessingStatus.ERROR
        attachment.save()
        raise self.retry(exc=exc, countdown=60)

    return f"Attachment {attachment_id} processed successfully."