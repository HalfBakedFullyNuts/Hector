"""Dog photo validation, storage, and thumbnailing (T-1001)."""

import io
from pathlib import Path

from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from hector.models.dog_profile import DogProfile

MAX_BYTES = 5 * 1024 * 1024
MAX_DIMENSION = 2000
THUMBNAIL_SIZE = 400
ALLOWED_FORMATS = {"JPEG", "PNG"}
CONTENT_TYPES = {"image/jpeg", "image/png"}


class PhotoValidationError(ValueError):
    """Raised when an upload violates the T-1001 constraints."""


def validate_photo(content_type: str | None, data: bytes) -> Image.Image:
    """Check size/type/pixels; return the decoded image on success."""
    assert data is not None
    if content_type not in CONTENT_TYPES:
        raise PhotoValidationError("Only JPEG or PNG images are allowed")
    if len(data) > MAX_BYTES:
        raise PhotoValidationError("Photo must be 5 MB or smaller")

    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception as exc:  # noqa: BLE001 - any decode failure is a 422
        raise PhotoValidationError("File is not a readable image") from exc

    if image.format not in ALLOWED_FORMATS:
        raise PhotoValidationError("Only JPEG or PNG images are allowed")
    if image.width > MAX_DIMENSION or image.height > MAX_DIMENSION:
        raise PhotoValidationError(f"Image must be at most {MAX_DIMENSION}x{MAX_DIMENSION}")

    return image


def store_photo(media_dir: Path, dog_id, dog_photo_url: str | None, image: Image.Image) -> str:
    """Write original + thumbnail, replacing any previous photo; returns URL."""
    dog_dir = media_dir / "dogs" / str(dog_id)
    dog_dir.mkdir(parents=True, exist_ok=True)

    _remove_previous(dog_dir, dog_photo_url)

    ext = "png" if image.format == "PNG" else "jpg"
    original_path = dog_dir / f"original.{ext}"
    thumb_path = dog_dir / f"thumb.{ext}"

    converted = image
    if ext == "jpg":
        converted = image.convert("RGB")

    converted.save(original_path)
    converted.copy().thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE))
    converted.save(thumb_path)

    return f"/media/dogs/{dog_id}/original.{ext}"


def _remove_previous(dog_dir: Path, dog_photo_url: str | None) -> None:
    """Delete files belonging to a previous upload of this dog."""
    if not dog_photo_url:
        return
    previous = Path(dog_photo_url.lstrip("/"))
    for suffix in ("jpg", "png"):
        candidate = dog_dir / previous.name.replace(previous.suffix.lstrip("."), suffix)
        candidate.unlink(missing_ok=True)


async def apply_photo_upload(
    db: AsyncSession,
    dog: DogProfile,
    content_type: str | None,
    data: bytes,
    media_dir: Path,
) -> str:
    """Validate + persist a new photo for the dog; returns its public URL."""
    assert dog.id is not None
    image = validate_photo(content_type, data)
    url = store_photo(media_dir, dog.id, dog.photo_url, image)

    dog.photo_url = url
    await db.commit()
    return url


def get_media_dir() -> Path:
    """Resolve the configured base directory for uploaded media."""
    from hector.config import get_settings

    return Path(get_settings().media_dir)
