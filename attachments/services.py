import hashlib
import magic
import imagehash
from PIL import Image
from django.core.files.base import ContentFile
from .models import Attachment
from django.db import transaction

from .tasks import process_attachment_pipeline

class AttachmentService:
    @staticmethod
    def get_file_hash(file_contents):
        """Generates SHA-256 hash for exact deduplication."""
        hash_sha256 = hashlib.sha256()
        for chunk in file_contents.chunks():
            hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    @staticmethod
    def get_perceptual_hash(file):
        """Generates pHash for images to find near-duplicates."""
        try:
            # Only attempt pHash for images
            img = Image.open(file)
            return str(imagehash.phash(img))
        except Exception:
            return None

    @classmethod
    def process_upload(cls, report, uploaded_file):
        sha256 = cls.get_file_hash(uploaded_file)
        
        uploaded_file.seek(0)
        file_sample = uploaded_file.read(2048)
        uploaded_file.seek(0)
        mime_type = magic.from_buffer(file_sample, mime=True)

        # Check for deduplication
        existing = Attachment.objects.filter(sha256_hash=sha256).first()

        # If it exists, we create a NEW record but reuse the EXISTING file to save disk space
        file_to_save = existing.file if existing else uploaded_file

        phash = None
        if 'image' in mime_type:
            phash = cls.get_perceptual_hash(uploaded_file)
            uploaded_file.seek(0)

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

        if existing and existing.processing_status == Attachment.ProcessingStatus.CLEAN:
            attachment.processing_status = Attachment.ProcessingStatus.CLEAN
            attachment.extracted_text = existing.extracted_text
            attachment.save()
        else:
            transaction.on_commit(lambda: process_attachment_pipeline.delay(attachment.id))

        return attachment, True