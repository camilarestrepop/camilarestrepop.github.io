"""``python -m cinco_tintas.intake`` — turn an "Add a product" issue into a product folder.

This is the easy way to add a piece to the shop: Cami fills in a form on github.com, drags her
photos into it, and presses Create. A GitHub Action runs this, which writes
``website/content/products/<name>/info.md`` plus the photos, and leaves a friendly comment on the
issue saying where the piece will appear.

Three things matter here more than anything else.

* **It never shows her a traceback.** A form with something missing, a photo that will not
  download, a collection that does not exist — each of those ends in a comment written in plain
  English, not a red cross with a Python error behind it.
* **A failed photo download does not lose her work.** ``info.md`` is written anyway and the comment
  tells her exactly where to drag the photos instead. That is the manual path, which always works.
* **The folder always lands directly under ``products/``.** The name she types is folded down to
  lowercase letters, numbers and dashes, so ``../../.github`` cannot become a path.

The photo downloader is injected, so the tests never touch the network.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from http.client import HTTPMessage
from io import BytesIO
from pathlib import Path
from typing import IO, Any, Protocol, override
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, OpenerDirector, Request, build_opener

from PIL import Image, UnidentifiedImageError

from .content import collection_slugs, slugify
from .errors import format_unexpected
from .paths import CONTENT_DIR, INFO_FILENAME, PRODUCTS_DIRNAME, PROJECT_ROOT

COMMENT_PATH = PROJECT_ROOT / "intake-comment.md"

DEFAULT_SITE_URL = "https://camilarestrepop.github.io"
DEFAULT_REPOSITORY = "camilarestrepop/camilarestrepop.github.io"

DOWNLOAD_TIMEOUT_SECONDS = 30
MAX_PHOTO_BYTES = 40_000_000
USER_AGENT = "Mozilla/5.0 (compatible; cinco-tintas-intake/1.0; +https://camilarestrepop.github.io)"

#: The issue form leaves one of these headings above every answer.
_HEADING = re.compile(r"^\s{0,3}#{2,4}\s+(?P<label>.+?)\s*$")
_NO_RESPONSE = re.compile(r"^_?no response_?$", re.IGNORECASE)

#: A photo dragged into the box becomes Markdown, or an <img> tag, or a plain link. All three count,
#: and one pass over the text keeps them in the order she dropped them in.
_PHOTO_IN_TEXT = re.compile(
    r"!\[[^\]]*\]\(\s*<?(?P<markdown>[^\s)<>]+)>?[^)]*\)"
    r"|<img\b[^>]*?\bsrc\s*=\s*[\"'](?P<html>[^\"']+)[\"']"
    r"|(?P<bare>https://[^\s<>\"')\]]+)",
    re.IGNORECASE,
)

#: Where a dragged-in photo can come from. Anything else is not fetched at all.
_ATTACHMENT_HOSTS = frozenset(
    {
        "user-images.githubusercontent.com",
        "private-user-images.githubusercontent.com",
        "objects.githubusercontent.com",
    }
)

_TRUE_ANSWERS = frozenset({"yes", "y", "si", "true", "sold-out", "agotado", "agotada", "1"})
_NONE_ANSWERS = frozenset({"", "none", "ninguna", "ninguno", "no", "n-a", "na"})

#: Every heading the form can produce, in either language, folded to a slug.
_FIELD_BY_HEADING: dict[str, str] = {
    "name": "name",
    "name-of-the-piece": "name",
    "nombre": "name",
    "nombre-de-la-pieza": "name",
    "sizes": "sizes",
    "sizes-you-have": "sizes",
    "tallas": "sizes",
    "sold-out": "sold_out",
    "agotado": "sold_out",
    "collection": "collection",
    "coleccion": "collection",
    "description-in-english": "english",
    "description": "english",
    "descripcion-en-ingles": "english",
    "description-in-spanish": "spanish",
    "descripcion-en-espanol": "spanish",
    "descripcion": "spanish",
    "photos": "photos",
    "fotos": "photos",
    "photos-of-the-piece": "photos",
}

#: What the site can serve, keyed by what the server says it sent.
_SUFFIX_BY_CONTENT_TYPE: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/heic": ".heic",
    "image/heif": ".heif",
    "image/tiff": ".tif",
}
_SUFFIX_BY_IMAGE_FORMAT: dict[str, str] = {
    "JPEG": ".jpg",
    "MPO": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
    "GIF": ".gif",
    "TIFF": ".tif",
    "HEIF": ".heic",
}


@dataclass(frozen=True, slots=True)
class ProductDraft:
    """What the issue form said, before anything is written to disk."""

    name: str
    sizes: str
    sold_out: bool
    collection_answer: str
    english: str
    spanish: str
    photo_urls: list[str]
    missing: list[str] = field(default_factory=list[str])

    @property
    def ready(self) -> bool:
        return not self.missing


@dataclass(frozen=True, slots=True)
class Download:
    """One fetched photo: the bytes, and what the server said they were."""

    content: bytes
    content_type: str = ""


class Downloader(Protocol):
    """How :func:`write_product` gets a photo. The tests pass a fake one."""

    def __call__(self, url: str) -> Download: ...


class DownloadRefused(Exception):
    """A photo address that will not be fetched, or an answer that is not a picture."""


@dataclass(frozen=True, slots=True)
class WriteResult:
    """What ended up on disk, and what did not."""

    slug: str
    folder: Path
    info_path: Path
    saved: list[str]
    failed: list[str]
    notes: list[str]

    @property
    def complete(self) -> bool:
        return not self.failed


def parse_issue_body(body: str) -> ProductDraft:
    """Read the filled-in issue form. Anything missing is listed rather than raised."""
    answers = _answers(body)
    name = _one_line(answers.get("name", ""))
    # If the photos heading is missing or renamed, look through the whole issue rather than give up.
    photo_urls = photo_urls_in(answers.get("photos") or body)

    missing: list[str] = []
    if not name:
        missing.append("name")
    if not photo_urls:
        missing.append("photos")

    return ProductDraft(
        name=name,
        sizes=_one_line(answers.get("sizes", "")),
        sold_out=slugify(answers.get("sold_out", "")) in _TRUE_ANSWERS,
        collection_answer=_one_line(answers.get("collection", "")),
        english=answers.get("english", "").strip(),
        spanish=answers.get("spanish", "").strip(),
        photo_urls=photo_urls,
        missing=missing,
    )


def _answers(body: str) -> dict[str, str]:
    """Split the issue body on its ``### Heading`` lines into one answer per form field."""
    found: dict[str, str] = {}
    current: str | None = None
    lines: list[str] = []

    def keep() -> None:
        if current is None:
            return
        text = "\n".join(lines).strip()
        if _NO_RESPONSE.match(text.strip()):
            text = ""
        if text or current not in found:
            found[current] = text

    for raw in body.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        heading = _HEADING.match(raw)
        if heading is not None:
            keep()
            current = _FIELD_BY_HEADING.get(slugify(heading.group("label")))
            lines = []
            continue
        if current is not None:
            lines.append(raw)
    keep()
    return found


def _one_line(value: str) -> str:
    """Form inputs are one line, but a pasted answer may not be. Flatten it."""
    return " ".join(value.split())


def photo_urls_in(text: str) -> list[str]:
    """Every photo address in the text, in the order she dragged them in, without repeats."""
    found: list[str] = []
    for match in _PHOTO_IN_TEXT.finditer(text):
        url = (match.group("markdown") or match.group("html") or match.group("bare") or "").strip().rstrip(".,;")
        if is_attachment_url(url) and url not in found:
            found.append(url)
    return found


def is_attachment_url(url: str) -> bool:
    """True only for the addresses GitHub gives a photo dragged into an issue.

    Everything else — another website, a local path, plain ``http`` — is refused rather than
    fetched, so a stranger's link in an issue cannot make the Action reach out to it.
    """
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    if parts.scheme != "https":
        return False
    host = (parts.hostname or "").lower()
    if host == "github.com":
        return parts.path.startswith("/user-attachments/")
    return host in _ATTACHMENT_HOSTS


def product_slug(name: str, *, products_dir: Path) -> str:
    """Fold the name she typed into a folder name, and make sure it is free.

    The result is always a single plain path piece, so nothing she can type — ``../../.github``,
    ``a/b``, ``...`` — can put the folder anywhere but straight inside ``products/``.
    """
    base = slugify(name) or "new-piece"
    slug = base
    number = 1
    while (products_dir / slug).exists():
        number += 1
        slug = f"{base}-{number}"
    return slug


def resolve_collection(answer: str, *, known: frozenset[str]) -> str | None:
    """Turn the dropdown answer into a real collection folder name, or nothing.

    The dropdown reads like ``Hasta los Huesos (hasta-los-huesos)``, so the name in brackets is
    tried first. An answer that matches no folder is dropped: a wrong ``collection:`` line would
    stop the website building, and a missing one only costs a link.
    """
    if slugify(answer) in _NONE_ANSWERS:
        return None
    candidates: list[str] = []
    bracketed = re.findall(r"\(([^()]+)\)", answer)
    candidates.extend(slugify(item) for item in bracketed)
    candidates.append(slugify(answer))
    for candidate in candidates:
        if candidate in known:
            return candidate
    whole = slugify(answer)
    return next((slug for slug in sorted(known, key=len, reverse=True) if slug and slug in whole), None)


def write_product(draft: ProductDraft, *, products_dir: Path, downloader: Downloader) -> WriteResult:
    """Create the product folder: ``info.md`` first, then as many photos as will come.

    ``info.md`` is written before any photo is fetched, so a download that fails still leaves the
    piece in the shop with its name and description — she only has to drag the photos in.
    """
    slug = product_slug(draft.name, products_dir=products_dir)
    folder = products_dir / slug
    # The slug cannot contain a slash, but prove the folder landed inside products/ rather than
    # trust that: this path comes from something a stranger could have typed into an issue.
    if folder.resolve().parent != products_dir.resolve():
        raise ValueError(f'"{draft.name}" does not make a folder name I can put inside products/.')
    folder.mkdir(parents=True, exist_ok=True)

    notes: list[str] = []
    known = collection_slugs(products_dir.parent)
    collection = resolve_collection(draft.collection_answer, known=known)
    if collection is None and slugify(draft.collection_answer) not in _NONE_ANSWERS:
        notes.append(
            f'I did not recognise the collection "{draft.collection_answer}", so I left it out. '
            "You can add it by hand in info.md."
        )

    info_path = folder / INFO_FILENAME
    info_path.write_text(info_file(draft, collection=collection), encoding="utf-8")

    saved: list[str] = []
    failed: list[str] = []
    for url in draft.photo_urls:
        name = _save_photo(url, folder=folder, number=len(saved) + 1, downloader=downloader)
        if name is None:
            failed.append(url)
        else:
            saved.append(name)

    return WriteResult(slug=slug, folder=folder, info_path=info_path, saved=saved, failed=failed, notes=notes)


def info_file(draft: ProductDraft, *, collection: str | None, now: datetime | None = None) -> str:
    """Write the product file in exactly the format the rest of the site reads."""
    day = (now or datetime.now(tz=UTC)).date().isoformat()
    lines = [
        f'# Added from an "Add a product" issue on {day}.',
        "# Change anything you like here and the website updates itself.",
        "# (Cambia lo que quieras aqui y la pagina se actualiza sola.)",
        "",
        f"name: {draft.name}",
        # An empty answer leaves the line in place so she can see where sizes go, but with no
        # trailing space after the colon.
        f"sizes: {draft.sizes}".rstrip(),
        f"sold out: {'yes' if draft.sold_out else 'no'}",
    ]
    if collection is not None:
        lines.append(f"collection: {collection}")
    lines.append(f"date: {day}")
    lines.extend(["", "--- ENGLISH ---", _body(draft.english), "", "--- ESPANOL ---", _body(draft.spanish), ""])
    return "\n".join(lines)


def _body(text: str) -> str:
    """Her description, kept as written, minus anything that would read as a language heading.

    A line like ``--- ENGLISH ---`` inside the description would split the file in the wrong place,
    so its dashes are shortened. It still reads the same to a person.
    """
    lines: list[str] = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        looks_like_marker = re.match(r"^\s*-{3,}\s*\w+\s*-{3,}\s*$", line) is not None
        lines.append(re.sub(r"-{3,}", "--", line) if looks_like_marker else line)
    return "\n".join(lines).strip()


def _save_photo(url: str, *, folder: Path, number: int, downloader: Downloader) -> str | None:
    """Fetch one photo into the folder as ``01.jpg``, ``02.png``… Returns None if it did not come."""
    try:
        download = downloader(url)
        suffix = _photo_suffix(download)
    except (DownloadRefused, URLError, TimeoutError, OSError, ValueError) as error:
        print(f"  could not save {url}: {type(error).__name__}: {error}")
        return None
    name = f"{number:02d}{suffix}"
    (folder / name).write_bytes(download.content)
    print(f"  saved {name}")
    return name


def _photo_suffix(download: Download) -> str:
    """What to call the file: what the server said, else what the bytes actually are."""
    from_header = _SUFFIX_BY_CONTENT_TYPE.get(download.content_type.strip().lower())
    if from_header is not None:
        return from_header
    try:
        with Image.open(BytesIO(download.content)) as opened:
            fmt = opened.format or ""
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise DownloadRefused(f"this is not a picture the website can use ({type(error).__name__})") from error
    suffix = _SUFFIX_BY_IMAGE_FORMAT.get(fmt.upper())
    if suffix is None:
        raise DownloadRefused(f"the website cannot use a {fmt or 'file'} picture; save it as a JPEG first")
    return suffix


def download_photo(url: str) -> Download:
    """Fetch a photo from GitHub: openly first, then signed in as the Action if that was refused."""
    try:
        return _fetch(url, token=None)
    except (URLError, TimeoutError, OSError):
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        if not token:
            raise
        return _fetch(url, token=token)


class CheckedRedirects(HTTPRedirectHandler):
    """Follow a redirect, but look at where it goes before carrying the sign-in header there.

    A GitHub attachment address does redirect — to a signed address on one of the image hosts — so
    redirects have to be followed for the easy way of adding a photo to work at all. What must not
    happen is the workflow's ``Authorization: Bearer $GITHUB_TOKEN`` travelling to wherever the
    redirect points: ``urllib`` copies every header onto the new request except ``Content-Length``
    and ``Content-Type``, so without this the token would go wherever the first host said.

    So each hop is put through :func:`is_attachment_url` again. A hop that stays on GitHub's
    attachment hosts keeps the header; one that leaves them is still followed — the picture may well
    be there — but stripped of the header first, and a hop that is not ``https`` at all is refused.
    """

    @override
    def redirect_request(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> Request | None:
        following = super().redirect_request(req, fp, code, msg, headers, newurl)
        if following is None:
            return None
        if urlsplit(newurl).scheme != "https":
            raise DownloadRefused(f"that photo's address sent me on to {newurl}, which is not a secure address")
        if not is_attachment_url(newurl) and following.has_header("Authorization"):
            following.remove_header("Authorization")
            print(f"  {newurl} is not one of GitHub's photo addresses, so I did not sign in to it")
        return following


def _checked_opener() -> OpenerDirector:
    """The fetcher every photo comes through: the one that checks each redirect, not only the first."""
    return build_opener(CheckedRedirects)


def _fetch(url: str, *, token: str | None) -> Download:
    if not is_attachment_url(url):
        raise DownloadRefused(f"{url} is not a photo uploaded to this repository, so I did not fetch it")
    headers = {"User-Agent": USER_AGENT, "Accept": "image/*,*/*"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers, method="GET")
    # The address was checked to be https on one of GitHub's own attachment hosts, and every
    # redirect it takes is checked again by CheckedRedirects above — which is what B310 is asking
    # about. The opener is built here rather than using urlopen precisely so that check is in place.
    response: Any = _checked_opener().open(request, timeout=DOWNLOAD_TIMEOUT_SECONDS)  # nosec B310
    try:
        content = bytes(response.read(MAX_PHOTO_BYTES + 1))
        content_type = str(response.headers.get_content_type())
    finally:
        response.close()
    if len(content) > MAX_PHOTO_BYTES:
        raise DownloadRefused("that photo is bigger than 40 MB; save a smaller copy and upload it by hand")
    return Download(content=content, content_type=content_type)


def site_url(repository: str) -> str:
    """The address the finished site lives at, worked out from ``owner/repo``.

    This is a user site and only a user site: the repository is named ``<owner>.github.io`` and the
    site is served from the root of it. That is what the 404 page depends on, since it writes its
    links from the site root, and it is the address Jack chose. A repository named anything else is
    not a layout this site supports, so the known address is the honest answer.
    """
    owner, _, repo = repository.partition("/")
    if repo.lower() == f"{owner.lower()}.github.io" and owner:
        return f"https://{repo.lower()}"
    return DEFAULT_SITE_URL


def upload_url(*, repository: str, slug: str) -> str:
    """The github.com page where photos can be dragged straight into the new folder."""
    return f"https://github.com/{repository}/upload/main/website/content/{PRODUCTS_DIRNAME}/{slug}"


def comment_for_missing(draft: ProductDraft) -> str:
    """The comment posted when the form was not filled in enough to add anything."""
    english = {"name": "the name of the piece", "photos": "at least one photo"}
    spanish = {"name": "el nombre de la pieza", "photos": "al menos una foto"}
    return "\n".join(
        [
            "I could not add the piece yet, because the form was missing:",
            "",
            *[f"- {english[item]}" for item in draft.missing],
            "",
            "Nothing on the website has changed. Edit this issue to fill those in and I will add it.",
            "",
            "---",
            "",
            "Todavia no pude anadir la pieza, porque en el formulario falta:",
            "",
            *[f"- {spanish[item]}" for item in draft.missing],
            "",
            "La pagina no ha cambiado. Edita este formulario con eso completo y la anado.",
            "",
        ]
    )


def comment_for(result: WriteResult, *, draft: ProductDraft, repository: str) -> str:
    """The comment posted when the piece was added, including what to do about missing photos."""
    page = f"{site_url(repository)}/product/{result.slug}.html"
    upload = upload_url(repository=repository, slug=result.slug)
    saved = len(result.saved)
    failed = len(result.failed)

    lines = [
        f"**{draft.name}** is on the website.",
        "",
        f"- Photos saved: {saved}",
        f"- Its page: {page}",
        f"- Its folder: `website/content/{PRODUCTS_DIRNAME}/{result.slug}/`",
        "",
        "Give it a minute or two: the website rebuilds itself, then refresh the page.",
    ]
    if failed:
        lines += [
            "",
            f"**{failed} photo(s) did not come through.** The piece is there, it just has "
            f"{'no photos' if saved == 0 else 'fewer photos'} yet.",
            "",
            f"To add them: open {upload} , drag the photos into that page, and press "
            '"Commit changes" at the bottom. Name them 01.jpg, 02.jpg, 03.jpg — the one called 01 '
            "is the big photo people see first.",
        ]
    for note in result.notes:
        lines += ["", note]

    lines += [
        "",
        "---",
        "",
        f"**{draft.name}** ya esta en la pagina.",
        "",
        f"- Fotos guardadas: {saved}",
        f"- Su pagina: {page}",
        f"- Su carpeta: `website/content/{PRODUCTS_DIRNAME}/{result.slug}/`",
        "",
        "Espera un minuto o dos: la pagina se reconstruye sola y luego la recargas.",
    ]
    if failed:
        lines += [
            "",
            f"**{failed} foto(s) no se pudieron guardar.** La pieza esta publicada, solo le faltan fotos.",
            "",
            f"Para anadirlas: abre {upload} , arrastra las fotos ahi y pulsa "
            '"Commit changes" abajo. Llamalas 01.jpg, 02.jpg, 03.jpg: la 01 es la foto grande.',
        ]
    lines.append("")
    return "\n".join(lines)


def _write_output(name: str, value: str) -> None:
    """Tell the workflow what happened, so it only closes the issue when there is a product."""
    path = os.environ.get("GITHUB_OUTPUT", "").strip()
    if not path:
        return
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def main() -> int:
    """Read the issue out of the environment, write the product, write the comment."""
    body = os.environ.get("ISSUE_BODY", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "").strip() or DEFAULT_REPOSITORY
    products_dir = CONTENT_DIR / PRODUCTS_DIRNAME

    try:
        draft = parse_issue_body(body)
        if not draft.ready:
            print(f"The form was missing: {', '.join(draft.missing)}. Nothing was written.")
            COMMENT_PATH.write_text(comment_for_missing(draft), encoding="utf-8")
            return 0

        print(f'Adding "{draft.name}" with {len(draft.photo_urls)} photo(s).')
        result = write_product(draft, products_dir=products_dir, downloader=download_photo)
        COMMENT_PATH.write_text(comment_for(result, draft=draft, repository=repository), encoding="utf-8")
        _write_output("product-created", "true")
        print(f"Wrote {result.info_path} with {len(result.saved)} photo(s); {len(result.failed)} did not come.")
        return 0
    except Exception as error:  # the issue still gets an answer, even if this program has a bug
        COMMENT_PATH.write_text(
            "\n".join(
                [
                    "Something went wrong inside the program that adds a piece, so nothing was published.",
                    "This is not a mistake in your form. Please send Jack this line:",
                    "",
                    f"    {type(error).__name__}: {error}",
                    "",
                    "---",
                    "",
                    "Algo fallo dentro del programa que anade la pieza, asi que no se publico nada.",
                    "No es un error tuyo. Por favor enviale a Jack esta linea:",
                    "",
                    f"    {type(error).__name__}: {error}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        print(format_unexpected(error))
        return 1


if __name__ == "__main__":
    sys.exit(main())
