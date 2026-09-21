from io import BytesIO
from pathlib import Path
import uuid
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.utils.deconstruct import deconstructible
from PIL import Image, ImageOps

def image_path(instance, filename):
    return f'{instance._meta.app_label}/{uuid.uuid4().hex}{Path(filename).suffix.lower()}'

def attachment_path(instance, filename):
    return f'quotes/{uuid.uuid4().hex}{Path(filename).suffix.lower()}'

@deconstructible
class PrivateStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=settings.PRIVATE_MEDIA_ROOT)

    def url(self, name):
        raise ValueError('Los adjuntos solo se descargan desde la vista autorizada.')

private_storage = PrivateStorage()

class OptimizedImageMixin:
    """Keep the original, create a bounded, metadata-free catalog derivative."""
    def save(self, *args, **kwargs):
        if self.image and not self.image._committed:
            self.image.seek(0)
            with Image.open(self.image) as original:
                im = ImageOps.exif_transpose(original).convert('RGB')
                im.thumbnail((900, 900))
                buf = BytesIO()
                im.save(buf, 'WEBP', quality=85)
            self.thumbnail.save(f'{uuid.uuid4().hex}.webp', ContentFile(buf.getvalue()), save=False)
            self.image.seek(0)
        super().save(*args, **kwargs)

    @property
    def display_image(self):
        return self.thumbnail or self.image
