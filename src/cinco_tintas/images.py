"""Turns whatever pictures get uploaded into two web-sized JPEGs each.

Cami uploads straight from her phone or her camera, so this has to cope with huge files, sideways
photos, and iPhone HEIC files. A picture that cannot be read is copied through untouched with a
notice rather than stopping the build.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from .errors import Report
from .model import Photo

LARGE_PIXELS = 1600
SMALL_PIXELS = 600
JPEG_QUALITY = 82


def _register_heic() -> bool:
    """iPhone photos only open if ``pillow-heif`` is installed, and it is optional on purpose."""
    try:
        import pillow_heif  # noqa: PLC0415 - an optional dependency has to be probed, not imported
    except ImportError:  # pragma: no cover - exercised only where the optional wheel is absent
        return False
    pillow_heif.register_heif_opener()  # pyright: ignore[reportPrivateImportUsage, reportUnknownMemberType]
    return True


HEIC_SUPPORTED = _register_heic()


@dataclass(frozen=True, slots=True)
class Derived:
    """The two files a photo turned into, as paths relative to ``dist/``."""

    large_url: str
    small_url: str


def derive_all(photos: list[Photo], *, dist_dir: Path, report: Report) -> None:
    """Write every photo's web sizes into ``dist/media`` and point the photo at them."""
    for photo in photos:
        derived = derive(photo, dist_dir=dist_dir, report=report)
        photo.large_url = derived.large_url
        photo.small_url = derived.small_url


def derive(photo: Photo, *, dist_dir: Path, report: Report) -> Derived:
    """Make the 1600px and 600px versions of one photo."""
    wanted = Derived(large_url=photo.large_url, small_url=photo.small_url)
    targets = [(dist_dir / wanted.large_url, LARGE_PIXELS), (dist_dir / wanted.small_url, SMALL_PIXELS)]

    if all(_is_up_to_date(target, source=photo.source) for target, _ in targets):
        return wanted

    try:
        with Image.open(photo.source) as opened:
            upright = ImageOps.exif_transpose(opened) or opened
            flattened = upright.convert("RGB")
            for target, pixels in targets:
                _write_jpeg(flattened, target=target, pixels=pixels)
    except (OSError, UnidentifiedImageError, ValueError, Image.DecompressionBombError) as error:
        # DecompressionBombError comes straight off Exception rather than OSError, so without naming
        # it here a single enormous photo would print "something went wrong inside the website
        # builder itself" — which is exactly the promise this module's docstring makes it keep.
        return _copy_through(photo, dist_dir=dist_dir, report=report, error=error)
    return wanted


def _write_jpeg(image: Image.Image, *, target: Path, pixels: int) -> None:
    resized = image.copy()
    if max(resized.size) > pixels:
        resized.thumbnail((pixels, pixels), Image.Resampling.LANCZOS)
    target.parent.mkdir(parents=True, exist_ok=True)
    resized.save(target, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)


def _is_up_to_date(target: Path, *, source: Path) -> bool:
    """Rebuilding 200 photos every time is slow, so skip the ones already newer than their source."""
    if not target.is_file():
        return False
    try:
        return target.stat().st_mtime >= source.stat().st_mtime
    except OSError:
        return False


def _copy_through(photo: Photo, *, dist_dir: Path, report: Report, error: Exception) -> Derived:
    """A picture we cannot read still goes on the site, exactly as uploaded."""
    hint = ""
    if photo.source.suffix.lower() in {".heic", ".heif"} and not HEIC_SUPPORTED:
        hint = " (this is an iPhone HEIC photo; saving it as JPEG first works best)"
    report.notice(
        where=photo.source,
        what=f"I could not resize this picture{hint}, so I used it exactly as it is. "
        f"It may load slowly on phones. Technical detail: {type(error).__name__}: {error}",
    )
    url = f"media/{photo.relative}"
    target = dist_dir / url
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(photo.source, target)
    return Derived(large_url=url, small_url=url)
