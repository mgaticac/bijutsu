from pathlib import PurePosixPath
from io import BytesIO
import math
import struct
import zipfile
from xml.etree import ElementTree
from PIL import Image
from django.conf import settings
from django.core.exceptions import ValidationError

ALLOWED = {'.stl', '.obj', '.3mf', '.zip', '.jpg', '.jpeg', '.png', '.webp'}
MIME = {
    '.stl': {'model/stl', 'application/sla', 'application/vnd.ms-pki.stl', 'application/octet-stream'},
    '.obj': {'model/obj', 'text/plain', 'application/octet-stream'},
    '.3mf': {'model/3mf', 'application/zip', 'application/octet-stream'},
    '.zip': {'application/zip', 'application/x-zip-compressed', 'application/octet-stream'},
    '.jpg': {'image/jpeg'}, '.jpeg': {'image/jpeg'}, '.png': {'image/png'}, '.webp': {'image/webp'},
}

def validate_content(data, suffix, nested=False):
    try:
        if suffix in {'.jpg', '.jpeg', '.png', '.webp'}:
            with Image.open(BytesIO(data)) as im:
                if im.width * im.height > 25_000_000:
                    raise ValueError()
                expected = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.webp': 'WEBP'}[suffix]
                if im.format != expected:
                    raise ValueError()
                im.verify()
        elif suffix == '.stl':
            if len(data) >= 84 and 84 + struct.unpack('<I', data[80:84])[0] * 50 == len(data):
                if len(data) == 84:
                    raise ValueError()
                return
            text = data.decode('ascii').strip()
            if not (text.startswith('solid') and 'facet normal' in text and 'vertex ' in text and 'endsolid' in text):
                raise ValueError()
        elif suffix == '.obj':
            lines = data.decode('utf-8-sig').splitlines()
            vertices = [line.split()[1:] for line in lines if line.startswith('v ')]
            if not vertices or not any(line.startswith('f ') for line in lines):
                raise ValueError()
            for vertex in vertices:
                if len(vertex) < 3 or not all(math.isfinite(float(v)) for v in vertex):
                    raise ValueError()
        elif suffix in {'.zip', '.3mf'}:
            if nested:
                raise ValueError()
            with zipfile.ZipFile(BytesIO(data)) as archive:
                members = archive.infolist()
                if not members or len(members) > 100 or sum(m.file_size for m in members) > settings.MAX_UPLOAD_BYTES * 4:
                    raise ValueError()
                model_found = False
                for member in members:
                    path = PurePosixPath(member.filename.replace('\\', '/'))
                    if path.is_absolute() or '..' in path.parts or ':' in str(path) or member.flag_bits & 1:
                        raise ValueError()
                    if member.is_dir():
                        continue
                    if member.file_size > settings.MAX_UPLOAD_BYTES or member.file_size / max(member.compress_size, 1) > 200:
                        raise ValueError()
                    payload = archive.read(member)
                    if suffix == '.zip':
                        if path.suffix.lower() not in ALLOWED - {'.zip', '.3mf'}:
                            raise ValueError()
                        validate_content(payload, path.suffix.lower(), nested=True)
                        model_found |= path.suffix.lower() in {'.obj', '.stl'}
                    else:
                        if path.suffix.lower() not in {'.xml', '.rels', '.model', '.png', '.jpg', '.jpeg'}:
                            raise ValueError()
                        if path.suffix.lower() in {'.xml', '.rels', '.model'}:
                            if b'<!DOCTYPE' in payload.upper() or b'<!ENTITY' in payload.upper():
                                raise ValueError()
                            root = ElementTree.fromstring(payload)
                            if path.suffix.lower() == '.model':
                                if root.tag.split('}')[-1] != 'model':
                                    raise ValueError()
                                model_found = True
                        else:
                            validate_content(payload, path.suffix.lower(), nested=True)
                if not model_found:
                    raise ValueError()
        else:
            raise ValueError()
    except (ValueError, UnicodeError, OSError, struct.error, zipfile.BadZipFile, RuntimeError, ElementTree.ParseError, Image.DecompressionBombError) as exc:
        raise ValidationError('El contenido no corresponde al formato permitido o el archivo está dañado.') from exc

def validate_attachment(file):
    suffix = PurePosixPath(file.name).suffix.lower()
    if suffix not in ALLOWED:
        raise ValidationError('Formatos permitidos: STL, OBJ, 3MF, ZIP, JPG, PNG y WebP.')
    if file.size == 0 or file.size > settings.MAX_UPLOAD_BYTES:
        raise ValidationError(f'Cada archivo debe pesar entre 1 byte y {settings.MAX_UPLOAD_BYTES // 1024 // 1024} MB.')
    mime = getattr(file, 'content_type', None)
    if mime and mime.split(';')[0].lower() not in MIME[suffix]:
        raise ValidationError('El tipo MIME no coincide con la extensión.')
    try:
        file.seek(0)
        validate_content(file.read(settings.MAX_UPLOAD_BYTES + 1), suffix)
    finally:
        file.seek(0)
