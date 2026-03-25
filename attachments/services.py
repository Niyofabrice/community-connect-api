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
        """
        The main ingestion entry point.
        Handles: Hashing, Magic Byte Validation, and Deduplication check.
        """
        # 1. Calculate SHA-256 Hash
        sha256 = cls.get_file_hash(uploaded_file)
        
        # 2. Check for Exact Deduplication (Storage-agnostic)
        # If the file already exists in our system, we link the existing record
        # or handle it according to business rules.
        existing = Attachment.objects.filter(sha256_hash=sha256).first()
        if existing:
            # Strategy: We could return the existing attachment to save storage,
            # or create a new reference to the same file.
            return existing, False 

        # 3. Identify True File Type (Magic Bytes)
        # This stops users from renaming 'virus.exe' to 'photo.jpg'
        file_sample = uploaded_file.read(2048)
        uploaded_file.seek(0) # Reset pointer
        mime_type = magic.from_buffer(file_sample, mime=True)

        # 4. Generate Perceptual Hash for images
        phash = None
        if 'image' in mime_type:
            phash = cls.get_perceptual_hash(uploaded_file)
            uploaded_file.seek(0)

        # 5. Create the Attachment instance (Set to PENDING for Celery)
        attachment = Attachment.objects.create(
            report=report,
            file=uploaded_file,
            file_name=uploaded_file.name,
            sha256_hash=sha256,
            phash=phash,
            mime_type=mime_type,
            processing_status=Attachment.ProcessingStatus.PENDING
        )

        if attachment:
            transaction.on_commit(lambda: process_attachment_pipeline.delay(attachment.id))

        return attachment, True