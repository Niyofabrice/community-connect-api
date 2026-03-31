import hashlib
import magic
import imagehash
import logging
from PIL import Image
from django.core.files.base import ContentFile
from .models import Attachment
from django.db import transaction

from .tasks import process_attachment_pipeline

logger = logging.getLogger('apps.attachments')

class AttachmentService:
    @staticmethod
    def get_file_hash(file_contents):
        """Generates SHA-256 hash for exact deduplication."""
        logger.debug(f"Generating SHA-256 for file: {getattr(file_contents, 'name', 'unknown')}")
        hash_sha256 = hashlib.sha256()
        for chunk in file_contents.chunks():
            hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    @staticmethod
    def get_perceptual_hash(file):
        """Generates pHash for images to find near-duplicates."""
        try:
            logger.debug(f"Generating SHA-256 for file: {getattr(file, 'name', 'unknown')}")
            img = Image.open(file)
            return str(imagehash.phash(img))
        except Exception as e:
            logger.warning(f"Failed to generate pHash: {str(e)}")
            return None

    @classmethod
    def process_upload(cls, report, uploaded_file):
        logger.info(f"Processing upload: {uploaded_file.name} for Report ID: {report.id}")
        sha256 = cls.get_file_hash(uploaded_file)
        
        uploaded_file.seek(0)
        file_sample = uploaded_file.read(2048)
        uploaded_file.seek(0)
        mime_type = magic.from_buffer(file_sample, mime=True)
        logger.debug(f"Detected MIME type: {mime_type}")

        # Check for deduplication
        existing = Attachment.objects.filter(sha256_hash=sha256).first()

        # If it exists, we create a NEW record but reuse the EXISTING file to save disk space
        file_to_save = existing.file if existing else uploaded_file

        phash = None
        if 'image' in mime_type:
            phash = cls.get_perceptual_hash(uploaded_file)
            uploaded_file.seek(0)

        try:
            attachment = Attachment.objects.create(
                report=report,
                file=file_to_save,
                file_name=uploaded_file.name,
                file_size=uploaded_file.size,
                sha256_hash=sha256,
                phash=phash,
                mime_type=mime_type,
                processing_status=Attachment.ProcessingStatus.PENDING
            )
            logger.info(f"Attachment record created (ID: {attachment.id})")
        except Exception as e:
            logger.error(f"Failed to create Attachment record: {str(e)}", exc_info=True)
            raise

        if existing and existing.processing_status == Attachment.ProcessingStatus.CLEAN:
            logger.info(f"Reusing processed data from existing attachment for ID: {attachment.id}")
            attachment.processing_status = Attachment.ProcessingStatus.CLEAN
            attachment.extracted_text = existing.extracted_text
            attachment.save()
        else:
            logger.info(f"Queueing processing pipeline for attachment {attachment.id}")
            transaction.on_commit(lambda: process_attachment_pipeline.delay(attachment.id))

        return attachment, True