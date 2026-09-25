import io

import pytest
from PIL import Image

from app import images


@pytest.fixture(autouse=True)
def media_root(tmp_path, monkeypatch):
    monkeypatch.setattr(images, "MEDIA_ROOT", tmp_path)
    return tmp_path


def encode(fmt, size=(1200, 800), exif=None):
    buf = io.BytesIO()
    Image.new("RGB", size, "red").save(buf, fmt, **({"exif": exif} if exif else {}))
    return buf.getvalue()


def test_jpeg_stored_as_is_with_thumbnail(media_root):
    data = encode("JPEG")
    stored = images.save("CD-0001", "front.jpg", data)
    assert stored["file_path"].startswith("items/CD-0001/") and stored["file_path"].endswith(".jpg")
    assert (media_root / stored["file_path"]).read_bytes() == data
    assert Image.open(media_root / stored["thumb_path"]).size == (400, 267)
    assert (stored["width"], stored["height"]) == (1200, 800)


def test_exif_rotation_applied_to_thumbnail_and_size():
    exif = Image.Exif()
    exif[0x0112] = 6
    stored = images.save("CD-0001", "sideways.jpg", encode("JPEG", exif=exif))
    assert (stored["width"], stored["height"]) == (800, 1200)
    assert Image.open(images.MEDIA_ROOT / stored["thumb_path"]).size == (400, 600)


def test_heic_converted_to_jpeg(media_root):
    stored = images.save("CD-0001", "photo.heic", encode("HEIF", size=(1000, 800)))
    assert stored["file_path"].endswith(".jpg")
    assert Image.open(media_root / stored["file_path"]).format == "JPEG"


def test_mpo_accepted_as_jpeg(media_root):
    buf = io.BytesIO()
    Image.new("RGB", (1200, 800), "red").save(buf, "MPO", save_all=True,
                                              append_images=[Image.new("RGB", (600, 400), "blue")])
    assert Image.open(io.BytesIO(buf.getvalue())).format == "MPO"
    stored = images.save("CD-0001", "IMG_1055.jpeg", buf.getvalue())
    assert stored["file_path"].endswith(".jpg")
    assert (media_root / stored["file_path"]).read_bytes() == buf.getvalue()
    assert Image.open(media_root / stored["thumb_path"]).size == (400, 267)


def test_small_image_thumbnail_not_upscaled():
    stored = images.save("CD-0001", "small.png", encode("PNG", size=(300, 200)))
    assert Image.open(images.MEDIA_ROOT / stored["thumb_path"]).size == (300, 200)


@pytest.mark.parametrize("name, data", [
    ("fake.jpg", b"this is not an image"),
    ("big.jpg", b"0" * (images.MAX_BYTES + 1)),
    ("anim.gif", encode("GIF")),
])
def test_rejected(media_root, name, data):
    with pytest.raises(images.ImageError):
        images.save("CD-0001", name, data)
    assert not any(media_root.rglob("*.*"))


def test_delete_files(media_root):
    stored = images.save("CD-0001", "x.png", encode("PNG"))
    images.delete_files(stored["file_path"], stored["thumb_path"], None)
    assert not any(media_root.rglob("*.*"))
