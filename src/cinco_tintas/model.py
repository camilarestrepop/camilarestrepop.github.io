"""The shapes the website is made of: bilingual text, photos, products, collections, runways."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import ClassVar, Literal

from markupsafe import Markup, escape

Language = Literal["en", "es"]
LANGUAGES: tuple[Language, ...] = ("en", "es")

_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")

SIZE_LADDER: tuple[str, ...] = ("XS", "S", "M", "L", "XL")


@dataclass(frozen=True, slots=True)
class Text:
    """One piece of writing in both languages.

    Spanish falls back to English at build time, so a half-translated site still reads.
    """

    en: str
    es: str

    @classmethod
    def of(cls, *, en: str, es: str) -> Text:
        english = en.strip()
        spanish = es.strip()
        return cls(en=english or spanish, es=spanish or english)

    @classmethod
    def empty(cls) -> Text:
        return cls(en="", es="")

    def __bool__(self) -> bool:
        return bool(self.en or self.es)

    def get(self, language: Language) -> str:
        return self.en if language == "en" else self.es

    def paragraphs(self, language: Language) -> list[Markup]:
        """Blank-line separated paragraphs, already escaped."""
        return paragraphs(self.get(language))


def paragraphs(body: str) -> list[Markup]:
    """Split a plain-text body into escaped paragraphs.

    A blank line starts a new paragraph. A plain line break inside a paragraph is just how the
    text was wrapped in the editor, so it becomes a space — pressing Enter mid-sentence on
    github.com cannot accidentally break the layout.

    Escaping happens here rather than in the template so that no stray ``<`` in the writing can
    ever turn into markup on the page.
    """
    chunks = [chunk.strip() for chunk in _PARAGRAPH_SPLIT.split(body.strip())]
    return [escape(" ".join(chunk.split())) for chunk in chunks if chunk]


@dataclass(slots=True)
class Photo:
    """One picture, plus the two sizes the site actually serves."""

    source: Path
    relative: str
    alt: Text
    large_url: str
    small_url: str

    @property
    def alt_text(self) -> str:
        """The description a screen reader reads out.

        The page carries both languages and hides one with CSS, but an ``alt`` attribute is one
        string and cannot do that, so when the two differ both are in it. Most of the time they are
        the same, because most pieces have one name.
        """
        return self.alt.en if self.alt.en == self.alt.es else f"{self.alt.en} / {self.alt.es}"

    @classmethod
    def create(cls, *, source: Path, relative: str, alt: Text) -> Photo:
        stem = relative.rsplit(".", 1)[0]
        return cls(
            source=source,
            relative=relative,
            alt=alt,
            large_url=f"media/{stem}-1600.jpg",
            small_url=f"media/{stem}-600.jpg",
        )


@dataclass(frozen=True, slots=True)
class VideoFile:
    """A video that sits in the folder and is played straight from the website."""

    source: Path
    relative: str
    url: str
    mime: str

    is_file: ClassVar[bool] = True


@dataclass(frozen=True, slots=True)
class VideoEmbed:
    """A video that lives on YouTube, Vimeo or Instagram and is shown through their player."""

    url: str

    is_file: ClassVar[bool] = False


@dataclass(frozen=True, slots=True)
class SiteConfig:
    """Everything from ``site.md`` — the details Cami changes most often."""

    brand_name: str
    tagline: Text
    instagram: str
    whatsapp: str
    email: str
    hero_photo: Photo | None
    carousel: list[Photo]
    latest_products_on_home: int

    @property
    def instagram_handle(self) -> str:
        return "@" + self.instagram.rstrip("/").rsplit("/", 1)[-1]

    @property
    def whatsapp_digits(self) -> str:
        return re.sub(r"\D", "", self.whatsapp)

    @property
    def whatsapp_display(self) -> str:
        return self.whatsapp


@dataclass(frozen=True, slots=True)
class Product:
    """One piece for sale. Price is never shown — every product is "price on request"."""

    slug: str
    name: Text
    sizes: list[str]
    sold_out: bool
    collection: str | None
    day: date
    body: Text
    photos: list[Photo]
    source: Path

    @property
    def cover(self) -> Photo | None:
        return self.photos[0] if self.photos else None

    @property
    def url(self) -> str:
        return f"product/{self.slug}.html"

    @property
    def size_options(self) -> list[SizeOption]:
        """The size row.

        When every listed size is an ordinary clothing size the whole ladder is shown, with the
        sizes she did not list greyed out. A one-off sizing (``Unique size``) is shown as written.
        """
        if not self.sizes:
            return []
        listed = {size.strip().upper() for size in self.sizes}
        if listed <= set(SIZE_LADDER):
            return [SizeOption(label=size, available=size in listed) for size in SIZE_LADDER]
        return [SizeOption(label=size, available=True) for size in self.sizes]


@dataclass(frozen=True, slots=True)
class SizeOption:
    """One circle in the size row on a product page."""

    label: str
    available: bool


SectionKind = Literal["collection", "runway"]


@dataclass(frozen=True, slots=True)
class Section:
    """A collection or a runway. They render from the same template with a different accent."""

    kind: SectionKind
    slug: str
    name: Text
    order: int
    body: Text
    photos: list[Photo]
    source: Path
    video: VideoFile | VideoEmbed | None = None
    collection: str | None = None

    @property
    def url(self) -> str:
        return f"{self.kind}/{self.slug}.html"

    @property
    def cover(self) -> Photo | None:
        return self.photos[0] if self.photos else None

    @property
    def coming_soon(self) -> bool:
        return not self.photos


@dataclass(slots=True)
class SiteContent:
    """Everything the templates need, already checked and sorted."""

    config: SiteConfig
    about: Text
    about_photo: Photo | None
    products: list[Product] = field(default_factory=list[Product])
    collections: list[Section] = field(default_factory=list[Section])
    runways: list[Section] = field(default_factory=list[Section])

    @property
    def all_photos(self) -> list[Photo]:
        found: dict[str, Photo] = {}
        for photo in self._iter_photos():
            found.setdefault(photo.relative, photo)
        return list(found.values())

    def _iter_photos(self) -> list[Photo]:
        photos: list[Photo] = []
        if self.config.hero_photo is not None:
            photos.append(self.config.hero_photo)
        if self.about_photo is not None:
            photos.append(self.about_photo)
        photos.extend(self.config.carousel)
        for product in self.products:
            photos.extend(product.photos)
        for section in (*self.collections, *self.runways):
            photos.extend(section.photos)
        return photos

    @property
    def latest_products(self) -> list[Product]:
        return self.products[: max(self.config.latest_products_on_home, 0)]

    @property
    def all_video_files(self) -> list[VideoFile]:
        """Every video that has to be copied onto the site, in the order the pages use them."""
        return [
            section.video for section in (*self.collections, *self.runways) if isinstance(section.video, VideoFile)
        ]

    def collection_by_slug(self, slug: str) -> Section | None:
        return next((item for item in self.collections if item.slug == slug), None)
