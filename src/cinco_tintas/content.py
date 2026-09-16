"""Reads the plain-text files in ``website/content`` and turns mistakes into friendly problems.

The file format is deliberately tiny: ``key: value`` lines at the top, then the description in
English and Spanish separated by ``--- ENGLISH ---`` / ``--- ESPANOL ---`` markers. No Markdown,
no YAML, nothing that can fail in a confusing way.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit

from .errors import Report
from .model import Photo, Product, Section, SectionKind, SiteConfig, SiteContent, Text
from .paths import (
    ABOUT_FILENAME,
    COLLECTIONS_DIRNAME,
    INFO_FILENAME,
    PRODUCTS_DIRNAME,
    RUNWAYS_DIRNAME,
    SHARED_DIRNAME,
    SITE_FILENAME,
    describe,
)
from .video import read_video

IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff", ".gif"})

#: A settings line. The leading ``\s*`` is deliberate: a line typed with a space or two in front of
#: it still reads as a setting, because nothing about the way it looks says it should not.
_KEY_LINE = re.compile(r"^\s*(?P<key>[A-Za-z][A-Za-z0-9 _-]{0,40}?)\s*:\s*(?P<value>.*)$")
_MARKER_LINE = re.compile(r"^\s*-{3,}\s*(?P<language>[a-z]+)\s*-{3,}\s*$")
_NUMBER_RUN = re.compile(r"(\d+)")
_SLUG_STRIP = re.compile(r"[^a-z0-9]+")
_SLUG_OK = re.compile(r"^[a-z0-9][a-z0-9-]*$")

_ENGLISH_WORDS = frozenset({"english", "en", "ingles", "eng"})
_SPANISH_WORDS = frozenset({"spanish", "espanol", "es", "spa"})

_TRUE_WORDS = frozenset({"yes", "y", "true", "t", "1", "si", "s", "sold", "sold out"})
_FALSE_WORDS = frozenset({"no", "n", "false", "f", "0", "none", "available"})


def strip_accents(value: str) -> str:
    """``Español`` -> ``Espanol`` so markers and answers work with or without accents."""
    return "".join(ch for ch in unicodedata.normalize("NFKD", value) if not unicodedata.combining(ch))


def normalise_key(key: str) -> str:
    """``Sold Out``, ``sold_out`` and ``sold out`` all mean the same thing."""
    cleaned = strip_accents(key).strip().lower().replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", cleaned)


def slugify(value: str) -> str:
    """Fold a folder name down to something safe to put in a web address."""
    cleaned = _SLUG_STRIP.sub("-", strip_accents(value).lower()).strip("-")
    return cleaned


def natural_key(name: str) -> tuple[object, ...]:
    """Sort ``2.jpg`` before ``10.jpg`` the way a person expects."""
    parts = _NUMBER_RUN.split(name.lower())
    return tuple(int(part) if part.isdigit() else part for part in parts)


@dataclass(slots=True)
class ParsedFile:
    """One content file, already split into its ``key: value`` lines and its two descriptions."""

    path: Path
    values: dict[str, str] = field(default_factory=dict[str, str])
    english: str = ""
    spanish: str = ""

    def get(self, key: str) -> str:
        return self.values.get(key, "").strip()

    def has(self, key: str) -> bool:
        return bool(self.get(key))

    @property
    def body(self) -> Text:
        return Text.of(en=self.english, es=self.spanish)


def parse_text(text: str, *, path: Path, report: Report, known_keys: frozenset[str]) -> ParsedFile:
    """Parse one content file. Unknown keys and odd lines become notices, never failures.

    The settings are the ``key: value`` lines at the top. Blank lines and ``#`` notes may sit among
    them — ``site.md`` is written that way — and a setting may be indented. The first line that is
    not one of the settings this kind of file knows starts the description, and from there **every**
    line is description text, even one shaped like ``Inspiracion: el mar``. That last part is what
    keeps a sentence with a colon in it on the page instead of quietly reading it as a setting and
    throwing it away.
    """
    parsed = ParsedFile(path=path)
    bodies: dict[str, list[str]] = {"en": [], "es": []}
    lines = text.splitlines()
    current: str | None = None
    in_header = True

    for number, raw in enumerate(lines, start=1):
        line = raw.rstrip()
        if line.lstrip().startswith("#"):
            continue

        language = _marker_language(line, number=number, path=path, report=report)
        if language is not None:
            if language:
                current, in_header = language, False
            continue

        if in_header:
            match = _KEY_LINE.match(line) if line.strip() else None
            shaped_like = normalise_key(match.group("key")) if match is not None else ""
            if match is not None and shaped_like in known_keys:
                if shaped_like in parsed.values:
                    report.notice(
                        where=path,
                        what=f'Line {number} sets "{shaped_like}" a second time. I kept the newer one.',
                    )
                parsed.values[shaped_like] = match.group("value").strip()
                continue
            blank = not line.strip()
            # Only a blank line or a settings-shaped line asks this question. A line of ordinary
            # writing is where the description starts, full stop — looking past it could only throw
            # her sentence away.
            # A blank line is still inside the settings when a setting OR the language heading comes
            # next; a settings-shaped line with a key this file does not use is a typo among the
            # settings ONLY when a real setting comes next — if the heading comes next it is her
            # first sentence and it stays.
            carries_on = _settings_carry_on_below(lines, index=number, known_keys=known_keys, heading_counts=blank)
            if (blank or shaped_like) and carries_on:
                if not blank:
                    report.notice(where=path, what=_ignored_line(number=number, key=shaped_like, keys=known_keys))
                continue
            in_header = False
            current = "en"
            if blank:
                continue
            if shaped_like:
                report.notice(where=path, what=_kept_line(number=number, key=shaped_like, keys=known_keys))

        if current is None:
            current = "en"
        _mention_a_setting_in_the_writing(line, number=number, path=path, report=report, known_keys=known_keys)
        bodies[current].append(line)

    parsed.english = "\n".join(bodies["en"]).strip()
    parsed.spanish = "\n".join(bodies["es"]).strip()
    return parsed


def _mention_a_setting_in_the_writing(
    line: str, *, number: int, path: Path, report: Report, known_keys: frozenset[str]
) -> None:
    """Say when a real setting is sitting in the description, where it shows up as words."""
    setting = _setting_key(line, known_keys=known_keys)
    if setting is None:
        return
    report.notice(
        where=path,
        what=f'Line {number} reads "{setting}: ...", but it is below where the settings stop, so it is part of '
        "the description and shows up in the words on the page. Move it up to the settings at the top of "
        "the file if you meant it as a setting.",
    )


def _marker_language(line: str, *, number: int, path: Path, report: Report) -> str | None:
    """``"en"`` or ``"es"`` for a language heading, ``""`` for one nobody can read, ``None`` for a
    line that is not a heading at all."""
    marker = _MARKER_LINE.match(strip_accents(line).lower())
    if marker is None:
        return None
    word = marker.group("language")
    if word in _ENGLISH_WORDS:
        return "en"
    if word in _SPANISH_WORDS:
        return "es"
    report.notice(
        where=path,
        what=f"Line {number} looks like a language heading but I do not know the language "
        f'"{word}". Use --- ENGLISH --- or --- ESPANOL ---.',
    )
    return ""


def _setting_key(line: str, *, known_keys: frozenset[str]) -> str | None:
    """The setting this line sets, if it is one this kind of file knows about."""
    match = _KEY_LINE.match(line)
    if match is None:
        return None
    key = normalise_key(match.group("key"))
    return key if key in known_keys else None


def _settings_carry_on_below(
    lines: list[str], *, index: int, known_keys: frozenset[str], heading_counts: bool = True
) -> bool:
    """True when more settings come after ``index`` — or, when ``heading_counts``, the language heading.

    This is what tells a blank line between two settings apart from the blank line before the
    writing starts, without asking the person typing the file to know the difference. For a blank
    line the heading counts as "still inside the settings"; for a settings-shaped line it must not,
    or a sentence with a colon written right before ``--- ESPANOL ---`` would be thrown away.
    """
    for raw in lines[index:]:
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if _MARKER_LINE.match(strip_accents(line).lower()) is not None:
            return heading_counts
        return _setting_key(line, known_keys=known_keys) is not None
    return False


def _ignored_line(*, number: int, key: str, keys: frozenset[str]) -> str:
    """Said about a settings-shaped line among the settings that names nothing this file uses."""
    return (
        f'Line {number} sets "{key}", which this kind of file does not use. I ignored it. '
        f"Known settings: {', '.join(sorted(keys))}."
    )


def _kept_line(*, number: int, key: str, keys: frozenset[str]) -> str:
    """Said about a settings-shaped line that turned out to be where the description starts."""
    return (
        f'Line {number} looks like a setting, but "{key}" is not one this kind of file uses, so I kept it as '
        f"part of the description. Known settings: {', '.join(sorted(keys))}."
    )


def read_file(path: Path, *, report: Report, known_keys: frozenset[str]) -> ParsedFile | None:
    """Read one content file from disk, reporting a friendly problem if it cannot be read."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        report.problem(
            where=path,
            what="I could not find this file.",
            fix=f"Create it, or check the spelling of the folder it should be in ({describe(path.parent)}).",
        )
        return None
    except UnicodeDecodeError:
        report.problem(
            where=path,
            what="This file is not saved as plain text, so I cannot read the words in it.",
            fix="Open it on github.com, copy the text into a new file, and save it again.",
        )
        return None
    return parse_text(text, path=path, report=report, known_keys=known_keys)


def parse_boolean(value: str, *, key: str, path: Path, report: Report, default: bool = False) -> bool:
    """Accept yes/no in either language, and say what is allowed when it is something else."""
    word = normalise_key(value)
    if not word:
        return default
    if word in _TRUE_WORDS:
        return True
    if word in _FALSE_WORDS:
        return False
    report.problem(
        where=path,
        what=f'"{key}: {value}" is not something I understand.',
        fix=f'Write "{key}: yes" or "{key}: no".',
    )
    return default


def parse_day(value: str, *, path: Path, report: Report) -> date | None:
    """Accept 2026-09-13, 2026-09, 2026 and 13/09/2026. Anything else is a friendly problem."""
    text = value.strip()
    if not text:
        return None
    patterns = ("%Y-%m-%d", "%Y-%m", "%Y", "%d/%m/%Y")
    for pattern in patterns:
        try:
            return date(*_parsed_parts(text, pattern))
        except ValueError:
            continue
    report.problem(
        where=path,
        what=f'"date: {value}" is not a date I can read.',
        fix="Write the date as year-month-day, like  date: 2026-09-13",
    )
    return None


def _parsed_parts(text: str, pattern: str) -> tuple[int, int, int]:
    """A calendar date has no time zone, so the naive parse is the right one here."""
    parsed = datetime.strptime(text, pattern)
    return parsed.year, parsed.month, parsed.day


def parse_whole_number(value: str, *, key: str, path: Path, report: Report, default: int) -> int:
    text = value.strip()
    if not text:
        return default
    try:
        return int(text)
    except ValueError:
        report.problem(
            where=path,
            what=f'"{key}: {value}" is not a whole number.',
            fix=f'Write a number, like "{key}: {default}".',
        )
        return default


def find_photos(folder: Path, *, content_dir: Path, name: Text, report: Report) -> list[Photo]:
    """Every picture in a folder, in the order a person would list them. The first one is the cover."""
    if not folder.is_dir():
        return []
    files = sorted(
        (item for item in folder.iterdir() if item.is_file() and item.suffix.lower() in IMAGE_SUFFIXES),
        key=lambda item: natural_key(item.name),
    )
    photos: list[Photo] = []
    # Only the part of the name before the dot decides what the picture is called on the website, so
    # 01.jpg and 01.png in one folder would both become the same file and one of them would quietly
    # never appear. That is the same kind of collision as two folders wanting one web address, and it
    # is treated the same way.
    first_with_stem: dict[str, Path] = {}
    for item in files:
        clash = first_with_stem.get(item.stem.lower())
        if clash is not None:
            report.problem(
                where=item,
                what=f'This and "{clash.name}" are in the same folder, and only the part before the dot is '
                f'used on the website ("{item.stem}"), so one of the two would never show up.',
                fix=f'Rename one of them, for example to "{item.stem}b{item.suffix.lower()}".',
            )
            continue
        first_with_stem[item.stem.lower()] = item
        mention_awkward_name(item, report=report)
        alt = Text.of(en=f"{name.en} — photo {len(photos) + 1}", es=f"{name.es} — foto {len(photos) + 1}")
        photos.append(Photo.create(source=item, relative=item.relative_to(content_dir).as_posix(), alt=alt))
    return photos


#: A file name that needs nothing done to it to go into a web address.
_PLAIN_FILENAME = re.compile(r"^[A-Za-z0-9._-]+$")


def mention_awkward_name(item: Path, *, report: Report) -> None:
    """Say so when a picture's name has to be rewritten to go into a web address.

    The address is written properly either way — a space becomes ``%20`` and a ``#`` becomes
    ``%23`` — so this is a note and not a problem. It is worth saying because a name like
    ``foto #1.jpg`` is the sort of thing that comes off a phone, and ``01.jpg`` is easier to live
    with when she comes back to the folder later.
    """
    if _PLAIN_FILENAME.match(item.name):
        return
    report.notice(
        where=item,
        what="The name of this picture has spaces or punctuation in it, so its web address has to be "
        "written in code (%20 and the like). It works, and the picture shows up. Renaming it to "
        "something like 01.jpg keeps the address readable.",
    )


SITE_KEYS = frozenset(
    {
        "brand name",
        "tagline",
        "tagline es",
        "instagram",
        "whatsapp",
        "email",
        "domain",
        "hero photo",
        "carousel folder",
        "latest products on home",
    }
)
ABOUT_KEYS = frozenset({"photo"})
PRODUCT_KEYS = frozenset({"name", "name es", "sizes", "sold out", "collection", "date"})
SECTION_KEYS = frozenset({"name", "name es", "order", "video", "collection"})


def load_site_config(content_dir: Path, *, report: Report) -> SiteConfig:
    """Read ``site.md`` — the brand name, the contact details, the hero photo."""
    path = content_dir / SITE_FILENAME
    parsed = read_file(path, report=report, known_keys=SITE_KEYS)
    if parsed is None:
        parsed = ParsedFile(path=path)

    brand_name = parsed.get("brand name")
    if not brand_name:
        report.problem(
            where=path,
            what="This file does not say what the brand is called.",
            fix="Add a line that reads   brand name: 5 TINTAS",
        )
        brand_name = "5 TINTAS"

    for key, example in (
        ("instagram", "https://instagram.com/5.tintas"),
        ("whatsapp", "+1 347 362 2979"),
        ("email", "camilarestrepo.fashionlab@gmail.com"),
    ):
        if not parsed.has(key):
            report.problem(
                where=path,
                what=f"This file does not have a {key} line, and the site shows it on every page.",
                fix=f"Add a line that reads   {key}: {example}",
            )

    name = Text.of(en=brand_name, es=brand_name)
    hero_photo = _named_photo(
        parsed.get("hero photo"), content_dir=content_dir, path=path, report=report, name=name, label="hero photo"
    )

    carousel_folder = parsed.get("carousel folder") or f"{SHARED_DIRNAME}/carousel"
    carousel_path = content_dir / carousel_folder
    if not carousel_path.is_dir():
        report.notice(
            where=path,
            what=f'There is no folder called "{carousel_folder}", so the home page carousel is empty. '
            "Add photos there to fill it.",
        )
        carousel: list[Photo] = []
    else:
        carousel = find_photos(carousel_path, content_dir=content_dir, name=name, report=report)

    return SiteConfig(
        brand_name=brand_name,
        tagline=Text.of(en=parsed.get("tagline"), es=parsed.get("tagline es")),
        instagram=checked_instagram(parsed.get("instagram"), path=path, report=report),
        whatsapp=checked_whatsapp(parsed.get("whatsapp"), path=path, report=report),
        email=checked_email(parsed.get("email"), path=path, report=report),
        domain=checked_domain(parsed.get("domain"), path=path, report=report),
        hero_photo=hero_photo,
        carousel=carousel,
        latest_products_on_home=parse_whole_number(
            parsed.get("latest products on home"),
            key="latest products on home",
            path=path,
            report=report,
            default=4,
        ),
    )


#: What an Instagram account name can be made of.
_INSTAGRAM_HANDLE = re.compile(r"^[A-Za-z0-9._]{1,30}$")

#: The hosts an Instagram profile address can live on.
_INSTAGRAM_HOSTS = frozenset({"instagram.com", "www.instagram.com", "m.instagram.com"})

#: A tap-to-chat number has to carry its country code, so anything shorter than this is a mistake.
WHATSAPP_LEAST_DIGITS = 10

#: One piece of a domain name: letters, digits and dashes, never starting or ending with a dash.
_DOMAIN_LABEL = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"

#: A whole domain name: at least two pieces, the last one starting with a letter, like  5tintas.com
_DOMAIN_NAME = re.compile(rf"^(?:{_DOMAIN_LABEL}\.)+[a-z][a-z0-9-]{{0,61}}[a-z0-9]$")


def checked_instagram(value: str, *, path: Path, report: Report) -> str:
    """The Instagram address, from whichever of the three ways she might have written it.

    These three lines sit in the footer of every page and in the "interested in this piece?" box of
    every product page, so one wrong character breaks every way of reaching her at once. A handle on
    its own (``@5.tintas``) is the most likely way to type it and the easiest to be sure about, so it
    is turned into the address and only noted; anything genuinely unusable is a problem naming the
    fix.
    """
    text = value.strip()
    if not text:
        return text
    # The app's own "copy link" produces https://www.instagram.com/5.tintas/?igsh=... and a profile
    # tab adds /reels/ — the account name is the first part of the path, and the rest is noise.
    parts = urlsplit(text if re.match(r"(?i)^https?://", text) else f"https://{text}")
    host = (parts.hostname or "").lower()
    if host in _INSTAGRAM_HOSTS:
        handle = parts.path.strip("/").split("/", 1)[0]
    elif "/" not in text and not re.match(r"(?i)^https?://", text):
        handle = text.lstrip("@")
    else:
        handle = ""
    if _INSTAGRAM_HANDLE.match(handle):
        address = f"https://instagram.com/{handle}"
        if address != text:
            report.notice(
                where=path,
                what=f'I read "instagram: {text}" as {address}, which is the web address of that account. '
                f"Write it that way on the line to be sure.",
            )
        return address
    report.problem(
        where=path,
        what=f'"instagram: {text}" is not an Instagram address, so the Instagram link on every page would '
        "go nowhere.",
        fix="Write the whole address, like   instagram: https://instagram.com/5.tintas",
    )
    return text


def checked_whatsapp(value: str, *, path: Path, report: Report) -> str:
    """The WhatsApp number, checked to have enough digits to be a real one."""
    text = value.strip()
    if not text:
        return text
    digits = re.sub(r"\D", "", text)
    if len(digits) >= WHATSAPP_LEAST_DIGITS:
        return text
    report.problem(
        where=path,
        what=f'"whatsapp: {text}" has only {len(digits)} digit(s) in it, which is not enough for a number '
        "WhatsApp can open. The country code has to be there too.",
        fix="Write the number with its country code, like   whatsapp: +1 347 362 2979",
    )
    return text


def checked_email(value: str, *, path: Path, report: Report) -> str:
    """The email address, checked to be one a mail program will accept."""
    text = value.strip()
    if not text:
        return text
    person, at, host = text.partition("@")
    if at and person and "." in host and not host.startswith(".") and not host.endswith("."):
        return text
    report.problem(
        where=path,
        what=f'"email: {text}" is not an email address, so the email link on every page would not open ' "anything.",
        fix="Write the whole address, like   email: camilarestrepo.fashionlab@gmail.com",
    )
    return text


def checked_domain(value: str, *, path: Path, report: Report) -> str:
    """The custom domain, as the bare hostname GitHub Pages wants in a ``CNAME`` file.

    The line is optional: no ``domain:`` line means no custom domain and no ``CNAME``, which is the
    right answer for a site that never buys one. What is written is normalised the way the other
    contact lines are — the scheme, a path, a port, a ``?...`` tail and a trailing dot are all noise
    around the name, and a person copying the address out of a browser brings some of them with it.

    A leading ``www.`` is **kept**. GitHub treats ``5tintas.com`` and ``www.5tintas.com`` as two
    different custom domains, so quietly dropping it would publish the site at an address other than
    the one set in the repository's settings. The host stays as it was written.

    Anything that cannot be a hostname returns "" rather than itself: it is also a problem, so the
    build stops before anything is written, and an empty answer can never become a wrong ``CNAME``.
    """
    text = value.strip()
    if not text:
        return ""
    try:
        parts = urlsplit(text if re.match(r"(?i)^https?://", text) else f"//{text}")
        # An "@" in the address part is a sign-in prefix as far as any address reader is concerned,
        # so "5tint@s.com" would otherwise quietly come back as the host "s.com". A domain has none.
        host = "" if "@" in parts.netloc else (parts.hostname or "").rstrip(".")
    except ValueError:
        host = ""
    if _DOMAIN_NAME.match(host):
        if host != text:
            report.notice(
                where=path,
                what=f'I read "domain: {text}" as {host}, which is the web address on its own. '
                f"Write it that way on the line to be sure.",
            )
        return host
    report.problem(
        where=path,
        what=f'"domain: {text}" is not a web address I can use, so I stopped rather than publish the site at '
        "the wrong one.",
        fix="Write the address on its own, like   domain: 5tintas.com   — or leave the line out and the site "
        "keeps its github.io address.",
    )
    return ""


def _named_photo(value: str, *, content_dir: Path, path: Path, report: Report, name: Text, label: str) -> Photo | None:
    """The picture a line like ``hero photo: shared/hero.jpg`` names.

    This is the one place where something typed in a file becomes a path on disk, so the path is
    worked out in full and then checked to be inside ``website/content``. A value with ``..`` in it
    would otherwise copy a file from outside the website onto the published site, and point at it
    from an address that is wrong on every page below the top one.
    """
    if not value:
        return None
    root = content_dir.resolve()
    source = (content_dir / value).resolve()
    if not source.is_relative_to(root):
        report.problem(
            where=path,
            what=f'The {label} "{value}" points at a file outside the website\'s own content folder.',
            fix=f"Upload the picture into website/content/ and write where it is from there, "
            f"like   {label}: {SHARED_DIRNAME}/hero.jpg",
        )
        return None
    if not source.is_file():
        report.problem(
            where=path,
            what=f'The {label} "{value}" is not there.',
            fix=f"Upload the picture into website/content/ and make the {label} line match its name exactly.",
        )
        return None
    mention_awkward_name(source, report=report)
    alt = Text.of(en=name.en, es=name.es)
    return Photo.create(source=source, relative=source.relative_to(root).as_posix(), alt=alt)


def load_about(content_dir: Path, *, report: Report) -> tuple[Text, Photo | None]:
    """Read ``about.md`` and the portrait that sits beside the story."""
    path = content_dir / ABOUT_FILENAME
    parsed = read_file(path, report=report, known_keys=ABOUT_KEYS)
    if parsed is None:
        return Text.empty(), None
    if not parsed.body:
        report.problem(
            where=path,
            what="The About page has no story in it.",
            fix="Write a few sentences under --- ENGLISH --- and under --- ESPANOL ---.",
        )
    name = Text.of(en="Camila Restrepo", es="Camila Restrepo")
    photo = _named_photo(
        parsed.get("photo"), content_dir=content_dir, path=path, report=report, name=name, label="photo"
    )
    return parsed.body, photo


def load_sections(
    content_dir: Path, *, kind: SectionKind, report: Report, known_collections: frozenset[str]
) -> list[Section]:
    """Read every collection folder (or every runway folder) into the shape the pages need."""
    folder = content_dir / (COLLECTIONS_DIRNAME if kind == "collection" else RUNWAYS_DIRNAME)
    sections: list[Section] = []
    seen: dict[str, Path] = {}

    for item in _content_folders(folder):
        if not_yet_a_page(item, report=report, template="_TEMPLATE-collection"):
            continue
        path = item / INFO_FILENAME
        parsed = read_file(path, report=report, known_keys=SECTION_KEYS)
        if parsed is None:
            continue
        slug = _folder_slug(item, report=report, seen=seen)
        if slug is None:
            continue
        name = _required_name(parsed, path=path, report=report, fallback=item.name, kind=kind)
        linked = _linked_collection(
            parsed.get("collection"), path=path, report=report, known_collections=known_collections
        )
        if kind == "collection" and parsed.has("collection"):
            report.notice(
                where=path,
                what='A collection does not need a "collection" line. I ignored it.',
            )
            linked = None
        order = parse_whole_number(parsed.get("order"), key="order", path=path, report=report, default=999)
        if not parsed.has("order"):
            report.notice(
                where=path,
                what='This has no "order" line, so it goes last. Add   order: 1   to put it first.',
            )
        sections.append(
            Section(
                kind=kind,
                slug=slug,
                name=name,
                order=order,
                body=parsed.body,
                photos=find_photos(item, content_dir=content_dir, name=name, report=report),
                source=path,
                video=read_video(item, link=parsed.get("video"), content_dir=content_dir, path=path, report=report),
                collection=linked,
            )
        )

    sections.sort(key=lambda section: (section.order, section.name.en.lower()))
    return sections


def load_products(content_dir: Path, *, report: Report, known_collections: frozenset[str]) -> list[Product]:
    """Read every product folder, newest first."""
    folder = content_dir / PRODUCTS_DIRNAME
    products: list[Product] = []
    seen: dict[str, Path] = {}

    for item in _content_folders(folder):
        if not_yet_a_page(item, report=report, template="_TEMPLATE-product"):
            continue
        path = item / INFO_FILENAME
        parsed = read_file(path, report=report, known_keys=PRODUCT_KEYS)
        if parsed is None:
            continue
        slug = _folder_slug(item, report=report, seen=seen)
        if slug is None:
            continue
        name = _required_name(parsed, path=path, report=report, fallback=item.name, kind="product")
        day = parse_day(parsed.get("date"), path=path, report=report)
        if day is None and not parsed.has("date"):
            day = date.today()
            report.notice(
                where=path,
                what='This has no "date" line, so I treated it as today and it shows first in the shop. '
                "Add   date: 2026-09-13   to place it yourself.",
            )
        photos = find_photos(item, content_dir=content_dir, name=name, report=report)
        if not photos:
            report.notice(
                where=path,
                what="There are no pictures in this folder yet, so the shop shows the name on its own. "
                "Upload photos into the same folder as this file.",
            )
        products.append(
            Product(
                slug=slug,
                name=name,
                sizes=[size.strip() for size in parsed.get("sizes").replace(";", ",").split(",") if size.strip()],
                sold_out=parse_boolean(parsed.get("sold out"), key="sold out", path=path, report=report),
                collection=_linked_collection(
                    parsed.get("collection"), path=path, report=report, known_collections=known_collections
                ),
                day=day or date.today(),
                body=parsed.body,
                photos=photos,
                source=path,
            )
        )

    # Newest first, and two pieces added on the same day read A to Z rather than backwards.
    products.sort(key=lambda product: product.slug)
    products.sort(key=lambda product: product.day, reverse=True)
    return products


def not_yet_a_page(folder: Path, *, report: Report, template: str) -> bool:
    """True when this folder has no ``info.md``, so there is nothing to publish from it yet.

    This is the half-finished state, and it must never stop the website being built. Uploading
    photos first and writing the words afterwards is a normal way to work, and moving an ``info.md``
    out of a folder is how a piece gets hidden, which leaves its photos behind. Both of those say
    "not ready", not "broken", so they earn a note and the build carries on.

    A folder with nothing in it at all says nothing worth saying, so it is passed over in silence.
    """
    if (folder / INFO_FILENAME).is_file():
        return False
    files = [item for item in folder.iterdir() if item.is_file()]
    if files:
        photos = any(item.suffix.lower() in IMAGE_SUFFIXES for item in files)
        what = "There are photos in here" if photos else "There are files in here"
        report.notice(
            where=folder,
            what=f"{what} but no {INFO_FILENAME}, so this is not on the website yet. "
            f"Copy website/content/{template}/{INFO_FILENAME} into this folder and fill it in.",
        )
    return True


def _content_folders(folder: Path) -> list[Path]:
    """Folders that hold real content. ``_`` and ``.`` prefixes are templates and housekeeping."""
    if not folder.is_dir():
        return []
    return sorted(
        item
        for item in folder.iterdir()
        if item.is_dir() and not item.name.startswith("_") and not item.name.startswith(".")
    )


def _folder_slug(folder: Path, *, report: Report, seen: dict[str, Path]) -> str | None:
    slug = slugify(folder.name)
    if not slug:
        report.problem(
            where=folder,
            what="I cannot make a web address out of this folder name.",
            fix="Rename the folder using plain lowercase letters, numbers and dashes, like  my-new-dress",
        )
        return None
    if not _SLUG_OK.match(folder.name):
        report.notice(
            where=folder,
            what=f'The web address for this will be "{slug}". Rename the folder to "{slug}" to match exactly.',
        )
    if slug in seen:
        report.problem(
            where=folder,
            what=f'This has the same web address ("{slug}") as {describe(seen[slug])}.',
            fix="Rename one of the two folders so each has its own name.",
        )
        return None
    seen[slug] = folder
    return slug


def _required_name(parsed: ParsedFile, *, path: Path, report: Report, fallback: str, kind: str) -> Text:
    english = parsed.get("name")
    if not english:
        report.problem(
            where=path,
            what=f"This {kind} does not have a name, and the name is what people see first.",
            fix=f"Add a line at the top that reads   name: {fallback.replace('-', ' ').title()}",
        )
        english = fallback.replace("-", " ").title()
    return Text.of(en=english, es=parsed.get("name es"))


def _linked_collection(value: str, *, path: Path, report: Report, known_collections: frozenset[str]) -> str | None:
    if not value:
        return None
    slug = slugify(value)
    if slug in known_collections:
        return slug
    choices = ", ".join(sorted(known_collections)) or "none yet"
    report.problem(
        where=path,
        what=f'"collection: {value}" does not match any collection folder.',
        fix=f"Use one of these instead: {choices}",
    )
    return None


def collection_slugs(content_dir: Path) -> frozenset[str]:
    """The collection folder names, used to check every ``collection:`` line points somewhere real."""
    return frozenset(slugify(item.name) for item in _content_folders(content_dir / COLLECTIONS_DIRNAME))


def load_content(content_dir: Path, *, report: Report) -> SiteContent:
    """Read the whole ``website/content`` folder."""
    known = collection_slugs(content_dir)
    config = load_site_config(content_dir, report=report)
    about, about_photo = load_about(content_dir, report=report)
    return SiteContent(
        config=config,
        about=about,
        about_photo=about_photo,
        products=load_products(content_dir, report=report, known_collections=known),
        collections=load_sections(content_dir, kind="collection", report=report, known_collections=known),
        runways=load_sections(content_dir, kind="runway", report=report, known_collections=known),
    )
