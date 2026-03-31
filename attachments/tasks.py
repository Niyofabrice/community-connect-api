import clamd
import pytesseract
import tempfile
import os
import logging
from PIL import Image
from pdf2image import convert_from_path
from celery import shared_task
from django.core.files.storage import default_storage
from .models import Attachment
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings

logger = logging.getLogger('apps.attachments')

def quarantine_file(attachment):
    """
    Physically moves the file from its current location to a restricted 
    quarantine folder and updates the file path in the database.
    """
    try:
        old_path = attachment.file.name
        filename = os.path.basename(old_path)
        new_path = os.path.join(settings.QUARANTINE_ROOT, filename)

        logger.warning(f"QUARANTINE TRIGGERED: Moving malicious file {filename} to {new_path}")

        with attachment.file.open('rb') as f:
            file_content = f.read()

        new_file_name = default_storage.save(new_path, ContentFile(file_content))

        attachment.file.name = new_file_name
        attachment.save(update_fields=['file'])

        if default_storage.exists(old_path):
            default_storage.delete(old_path)
        
        logger.info(f"File {filename} successfully moved to quarantine.")
    except Exception as e:
        logger.error(f"FAILED TO QUARANTINE FILE {attachment.id}: {str(e)}", exc_info=True)

@shared_task(bind=True, max_retries=3)
def process_attachment_pipeline(self, attachment_id):
    logger.info(f"STARTING PIPELINE for Attachment ID: {attachment_id} (Attempt {self.request.retries + 1})")
    try:
        attachment = Attachment.objects.get(id=attachment_id)
    except Attachment.DoesNotExist:
        logger.error(f"ABORTING: Attachment {attachment_id} not found in database.")
        return f"Attachment {attachment_id} not found."

    attachment.processing_status = Attachment.ProcessingStatus.SCANNING
    attachment.save(update_fields=['processing_status'])

    try:
        logger.debug(f"Connecting to ClamAV for attachment {attachment_id}...")
        cd = clamd.ClamdNetworkSocket(host='clamav', port=3310)
        with attachment.file.open('rb') as f:
            scan_result = cd.instream(f)

        if scan_result and scan_result['stream'][0] == 'FOUND':
            virus_name = scan_result['stream'][1]
            logger.critical(f"MALWARE DETECTED in Attachment {attachment_id}: {virus_name}")
            attachment.processing_status = Attachment.ProcessingStatus.MALICIOUS
            attachment.save(update_fields=['processing_status'])

            quarantine_file(attachment)
            return f"Virus {virus_name} found in {attachment_id}"
        
        logger.info(f"Scan CLEAN for attachment {attachment_id}. Starting OCR.")

        extracted_text = ""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            with attachment.file.open('rb') as f:
                tmp_file.write(f.read())
            tmp_path = tmp_file.name

        try:
            if 'image' in attachment.mime_type:
                logger.debug(f"Running Tesseract OCR on Image: {attachment_id}")
                with Image.open(tmp_path) as img:
                    extracted_text = pytesseract.image_to_string(img)

            elif 'pdf' in attachment.mime_type:
                logger.debug(f"Converting PDF to images for OCR: {attachment_id}")
                images = convert_from_path(tmp_path)
                for img in images:
                    extracted_text += pytesseract.image_to_string(img) + "\n"
            
            logger.info(f"OCR Complete for {attachment_id}. Length: {len(extracted_text)} chars.")

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        attachment.extracted_text = extracted_text
        attachment.processing_status = Attachment.ProcessingStatus.CLEAN
        attachment.save(update_fields=['extracted_text', 'processing_status'])

        logger.info(f"SUCCESS: Attachment {attachment_id} fully processed.")

    except Exception as exc:
        logger.error(f"PIPELINE ERROR on Attachment {attachment_id}: {str(exc)}", exc_info=True)
        attachment.processing_status = Attachment.ProcessingStatus.ERROR
        attachment.save(update_fields=['processing_status'])

        logger.info(f"Retrying task for Attachment {attachment_id} in 60 seconds...")
        raise self.retry(exc=exc, countdown=60)

    return f"Attachment {attachment_id} processed successfully."