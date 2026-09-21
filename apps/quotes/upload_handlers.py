from django.conf import settings
from django.core.exceptions import RequestDataTooBig
from django.core.files.uploadhandler import FileUploadHandler

class BoundedUploadHandler(FileUploadHandler):
    """Bound streamed uploads before writing arbitrarily large temporary files."""
    def __init__(self, request=None):
        super().__init__(request)
        self.total = 0
        self.current = 0

    def new_file(self, *args, **kwargs):
        super().new_file(*args, **kwargs)
        self.current = 0

    def receive_data_chunk(self, raw_data, start):
        self.current += len(raw_data)
        self.total += len(raw_data)
        if self.current > settings.MAX_UPLOAD_BYTES or self.total > settings.MAX_UPLOAD_BYTES * 5:
            raise RequestDataTooBig('Se excedió el límite de archivos adjuntos.')
        return raw_data

    def file_complete(self, file_size):
        return None
