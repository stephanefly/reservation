import os
import re
from uuid import uuid4

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.text import slugify

IMAGE_FORMATS = {
    "JPEG": ("jpg", "image/jpeg"),
    "PNG": ("png", "image/png"),
    "WEBP": ("webp", "image/webp"),
    "GIF": ("gif", "image/gif"),
}
CONTENT_TYPES = {extension: content_type for extension, content_type in IMAGE_FORMATS.values()}
IMAGE_NAME = r"[0-9a-f]{32}-[a-z0-9_-]{1,64}\.(?:jpg|png|webp|gif)"


def image_storage():
    return FileSystemStorage(
        location=os.environ.get("NEWSLETTER_IMAGE_ROOT") or settings.BASE_DIR / "donnees" / "newsletter-images"
    )


def store_image(storage, upload):
    stem = upload.name.rsplit(".", 1)[0]
    label = slugify(stem)[:64] or "image"
    extension, _ = IMAGE_FORMATS[upload.image.format]
    return storage.save(f"{uuid4().hex}-{label}.{extension}", upload)


def listed_images(storage):
    if not storage.exists(""):
        return []
    _, files = storage.listdir("")
    names = [name for name in files if re.fullmatch(IMAGE_NAME, name)]
    return sorted(names, key=storage.get_modified_time, reverse=True)
