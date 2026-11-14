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

    _make_thumb(upright, thumb)

    return {
        "file_path": original.relative_to(MEDIA_ROOT).as_posix(),
        "thumb_path": thumb.relative_to(MEDIA_ROOT).as_posix(),
        "width": upright.width,
        "height": upright.height,
    }


def _make_thumb(upright, thumb):
    preview = upright.convert("RGB")
    if preview.width > THUMB_WIDTH:
        preview = preview.resize((THUMB_WIDTH, round(preview.height * THUMB_WIDTH / preview.width)),
                                 Image.Resampling.LANCZOS)
    preview.save(thumb, "JPEG", quality=85)


def scan(create_thumbs=True):
    """Find stored originals under MEDIA_ROOT/items/<ID>/, oldest first per item.

    Returns (found, problems). Each found entry has item_id plus the same fields save() returns.
    A missing thumbnail is regenerated unless create_thumbs is False.
    """
    found, problems = [], []
    items_dir = MEDIA_ROOT / "items"
    if not items_dir.is_dir():
        return found, problems
    for folder in sorted(p for p in items_dir.iterdir() if p.is_dir()):
        originals = [p for p in folder.iterdir()
                     if p.is_file() and not p.name.startswith(".") and not p.stem.endswith("_thumb")]
        for original in sorted(originals, key=lambda p: (p.stat().st_mtime, p.name)):
            rel = original.relative_to(MEDIA_ROOT).as_posix()
            if original.suffix.lower().lstrip(".") not in set(FORMATS.values()):
                problems.append(f"{rel}: not an image file, skipped")
                continue
            try:
                with Image.open(original) as image:
                    upright = ImageOps.exif_transpose(image)
                    thumb = folder / f"{original.stem}_thumb.jpg"
                    if not thumb.exists() and create_thumbs:
                        _make_thumb(upright, thumb)
                    width, height = upright.width, upright.height
            except Exception:
                problems.append(f"{rel}: not a readable image, skipped")
                continue
            found.append({
                "item_id": folder.name,
                "file_path": rel,
                "thumb_path": thumb.relative_to(MEDIA_ROOT).as_posix(),
                "width": width,
                "height": height,
            })
    return found, problems


def delete_files(*relative_paths):
    for rel in relative_paths:
        if rel:
            (MEDIA_ROOT / rel).unlink(missing_ok=True)
