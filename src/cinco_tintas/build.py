"""Builds the whole website into ``dist/``."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .content import load_content
from .errors import Report
from .images import derive_all
from .model import Section, SiteContent
from .paths import CONTENT_DIR, DIST_DIR, THEME_DIR
from .render import Page, make_environment, write_pages
from .video import copy_all as copy_videos

COLLECTION_ACCENT = "#bfd128"
RUNWAY_ACCENT = "#bdafd0"

_PAGE_FOLDERS = ("collection", "runway", "product", "static")


@dataclass(frozen=True, slots=True)
class BuildResult:
    """What the build produced, for the message printed at the end."""

    dist_dir: Path
    pages: list[Path]
    photo_count: int
    report: Report

    @property
    def index(self) -> Path:
        return self.dist_dir / "index.html"


def build_site(
    *, content_dir: Path = CONTENT_DIR, theme_dir: Path = THEME_DIR, dist_dir: Path = DIST_DIR
) -> BuildResult:
    """Read the content, check it, and write the finished site.

    Raises :class:`~cinco_tintas.errors.ContentProblems` if the content has mistakes in it. A
    half-built site never replaces a working one: every mistake in the writing is found first, and
    then the pictures and the videos are made — both of which only ever write inside ``media/`` —
    so by the time last build's pages are deleted, everything that could still fail already has.
    """
    report = Report()
    content = load_content(content_dir, report=report)
    report.raise_if_problems()

    photos = content.all_photos
    videos = content.all_video_files
    dist_dir.mkdir(parents=True, exist_ok=True)
    derive_all(photos, dist_dir=dist_dir, report=report)
    copy_videos(videos, dist_dir=dist_dir, report=report)
    report.raise_if_problems()
    _clear_generated(dist_dir)
    _prune_media(
        dist_dir,
        keep={photo.large_url for photo in photos}
        | {photo.small_url for photo in photos}
        | {video.url for video in videos},
    )
    _copy_static(theme_dir=theme_dir, dist_dir=dist_dir)

    environment = make_environment(templates_dir=theme_dir / "templates")
    pages = write_pages(plan_pages(content), environment=environment, content=content, dist_dir=dist_dir)
    return BuildResult(dist_dir=dist_dir, pages=pages, photo_count=len(photos), report=report)


def plan_pages(content: SiteContent) -> list[Page]:
    """Every page the site has, in the order they are written."""
    pages: list[Page] = [
        Page(output="index.html", template="home.html", context={"body_class": "page-home"}),
        Page(output="shop.html", template="shop.html", context={"body_class": "page-shop"}),
        Page(output="collections.html", template="collections_index.html", context={"body_class": "page-index"}),
        Page(output="runways.html", template="runways_index.html", context={"body_class": "page-index"}),
        Page(output="about.html", template="about.html", context={"body_class": "page-about"}),
        Page(output="contact.html", template="contact.html", context={"body_class": "page-contact"}),
        # The only page linked from the site root: it answers for addresses in every folder.
        Page(output="404.html", template="404.html", context={"body_class": "page-404"}, absolute_urls=True),
    ]
    for section in content.collections:
        pages.append(_section_page(section, content=content))
    for section in content.runways:
        pages.append(_section_page(section, content=content))
    for product in content.products:
        pages.append(
            Page(
                output=product.url,
                template="product.html",
                context={"product": product, "body_class": "page-product"},
            )
        )
    return pages


def _section_page(section: Section, *, content: SiteContent) -> Page:
    linked = content.collection_by_slug(section.collection) if section.collection else None
    return Page(
        output=section.url,
        template="collection.html",
        context={
            "section": section,
            "accent": COLLECTION_ACCENT if section.kind == "collection" else RUNWAY_ACCENT,
            "linked_collection": linked,
            "current_section": section.slug,
            "body_class": f"page-{section.kind}",
        },
    )


def _clear_generated(dist_dir: Path) -> None:
    """Remove last build's pages so a deleted product cannot linger. ``media/`` is kept as a cache."""
    dist_dir.mkdir(parents=True, exist_ok=True)
    for item in dist_dir.glob("*.html"):
        item.unlink()
    for name in _PAGE_FOLDERS:
        shutil.rmtree(dist_dir / name, ignore_errors=True)


def _prune_media(dist_dir: Path, *, keep: set[str]) -> None:
    """Delete derived pictures whose original is gone."""
    media = dist_dir / "media"
    if not media.is_dir():
        return
    wanted = {(dist_dir / url).resolve() for url in keep}
    for item in sorted(media.rglob("*"), reverse=True):
        if item.is_file() and item.resolve() not in wanted:
            item.unlink()
        elif item.is_dir() and not any(item.iterdir()):
            item.rmdir()


def _copy_static(*, theme_dir: Path, dist_dir: Path) -> None:
    static = theme_dir / "static"
    if static.is_dir():
        shutil.copytree(static, dist_dir / "static", dirs_exist_ok=True)


def describe_result(result: BuildResult) -> str:
    """The cheerful summary printed when everything worked."""
    return "\n".join(
        [
            "",
            f"Done. I built {len(result.pages)} pages and {result.photo_count} pictures.",
            "",
            f"Have a look: open {result.index}",
            "",
        ]
    )
