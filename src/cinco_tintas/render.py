"""Turns the content into HTML pages with Jinja2.

Every link is written relative to the page it appears on, so ``dist/`` opens correctly both from a
``file://`` path on a laptop and from the live address on GitHub Pages.
"""

from __future__ import annotations

import posixpath
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from .model import SiteConfig, SiteContent


@dataclass(frozen=True, slots=True)
class Page:
    """One HTML file to write, and what goes on it.

    ``absolute_urls`` writes this page's links from the site root instead of from the page.
    GitHub Pages serves the 404 page for any address that does not exist, deep ones like
    ``/product/gone.html`` included, so a relative link there would be resolved against a folder
    the browser only imagined. Every other page stays relative, which is what lets ``dist/``
    browse identically from a laptop and from the live address.
    """

    output: str
    template: str
    context: dict[str, Any] = field(default_factory=dict[str, Any])
    absolute_urls: bool = False


#: Path pieces that are structure rather than a name, so they are never encoded.
_UNENCODED_PARTS = frozenset({"", ".", ".."})


def encode_url(target: str) -> str:
    """Write a path the way a browser has to read it.

    A photo called ``foto #1.jpg`` is a perfectly ordinary name on a computer, but in an address the
    ``#`` starts a fragment and the space ends the address, so the picture would 404 while the build
    stayed green. Each piece of the path is percent-encoded, and only the pieces: the slashes and
    any ``..`` have to survive as themselves for the address to still point where it did.
    """
    return "/".join(part if part in _UNENCODED_PARTS else quote(part, safe="") for part in target.split("/"))


def relative_url(target: str, *, from_page: str) -> str:
    """``shop.html`` seen from ``collection/eva.html`` is ``../shop.html``, ready for an attribute."""
    here = posixpath.dirname(from_page) or "."
    return encode_url(posixpath.relpath(target, here))


def whatsapp_url(config: SiteConfig, message: str) -> str:
    """A tap-to-chat link that opens WhatsApp with the message already typed."""
    return f"https://wa.me/{config.whatsapp_digits}?text={quote(message)}"


def mailto_url(config: SiteConfig, subject: str) -> str:
    return f"mailto:{config.email}?subject={quote(subject)}"


def make_environment(*, templates_dir: Path) -> Environment:
    """A strict Jinja environment: unknown names fail loudly here rather than silently on the site."""
    return Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(default=True, default_for_string=True),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def render_page(page: Page, *, environment: Environment, content: SiteContent) -> str:
    """Render one page, with every helper it needs already bound to that page's location."""
    template = environment.get_template(page.template)
    config = content.config

    def page_url(target: str) -> str:
        if page.absolute_urls:
            return "/" + encode_url(target)
        return relative_url(target, from_page=page.output)

    def page_whatsapp_url(message: str) -> str:
        return whatsapp_url(config, message)

    def page_mailto_url(subject: str) -> str:
        return mailto_url(config, subject)

    context: dict[str, Any] = {
        "site": config,
        "content": content,
        "url": page_url,
        "whatsapp_url": page_whatsapp_url,
        "mailto_url": page_mailto_url,
        "current_section": None,
        "body_class": "",
    }
    context.update(page.context)
    return template.render(**context)


def write_pages(pages: list[Page], *, environment: Environment, content: SiteContent, dist_dir: Path) -> list[Path]:
    """Render every page and write it into ``dist/``."""
    written: list[Path] = []
    for page in pages:
        target = dist_dir / page.output
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_page(page, environment=environment, content=content), encoding="utf-8")
        written.append(target)
    return written
