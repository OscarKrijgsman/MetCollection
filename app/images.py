import io
import uuid
from pathlib import Path

import pillow_heif
from PIL import Image, ImageOps

pillow_heif.register_heif_opener()

MEDIA_ROOT = Path(__file__).resolve().parent.parent / "media"
MAX_BYTES = 20 * 1024 * 1024
THUMB_WIDTH = 400
# Pillow format -> extension the original is stored with. HEIF is converted to JPEG.
# MPO is a JPEG with extra frames appended (iPhone depth/HDR data); browsers show the first frame.
FORMATS = {"JPEG": "jpg", "MPO": "jpg", "PNG": "png", "WEBP": "webp", "HEIF": "jpg"}


class ImageError(ValueError):
    pass


def save(item_id, filename, data):
    """Validate an uploaded file and store it with a thumbnail. Returns paths relative to MEDIA_ROOT."""
    if len(data) > MAX_BYTES:
        raise ImageError(f"{filename}: larger than {MAX_BYTES // (1024 * 1024)} MB")
    try:
        with Image.open(io.BytesIO(data)) as probe:
            fmt = probe.format
            probe.verify()
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception:
        raise ImageError(f"{filename}: not a readable image")
    if fmt not in FORMATS:
        raise ImageError(f"{filename}: {fmt} is not supported, use JPEG, PNG, WebP or HEIC")

    folder = MEDIA_ROOT / "items" / item_id
    folder.mkdir(parents=True, exist_ok=True)
    stem = uuid.uuid4().hex[:12]
    original = folder / f"{stem}.{FORMATS[fmt]}"
    thumb = folder / f"{stem}_thumb.jpg"

    upright = ImageOps.exif_transpose(image)
    if fmt == "HEIF":
        upright.convert("RGB").save(original, "JPEG", quality=92)
    else:
        original.write_bytes(data)

    preview = upright.convert("RGB")
    if preview.width > THUMB_WIDTH:
        preview = preview.resize((THUMB_WIDTH, round(preview.height * THUMB_WIDTH / preview.width)),
                                 Image.Resampling.LANCZOS)
    preview.save(thumb, "JPEG", quality=85)

    return {
        "file_path": original.relative_to(MEDIA_ROOT).as_posix(),
        "thumb_path": thumb.relative_to(MEDIA_ROOT).as_posix(),
        "width": upright.width,
        "height": upright.height,
    }


def delete_files(*relative_paths):
    for rel in relative_paths:
        if rel:
            (MEDIA_ROOT / rel).unlink(missing_ok=True)
