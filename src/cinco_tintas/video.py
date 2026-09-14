"""The one video that can sit under the photos of a collection or a runway show.

There are two ways to have one, and Cami picks whichever suits the video she has:

* drop a file called ``video.mp4`` (or ``.mov``, or ``.webm``) into the folder, or
* paste the ordinary address-bar link of a YouTube, Vimeo or Instagram page into ``info.md``.

The link she pastes is the one she can actually get to: the address in the bar of the browser,
not the embed address hidden under Share. Turning that into something a page can show is this
module's whole job, so that nobody has to be told about "embed codes".

A file in the folder wins over a link, because a file is the more deliberate act of the two.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .errors import Report
from .model import VideoEmbed, VideoFile

#: The video files a browser can play without any help.
VIDEO_SUFFIXES: tuple[str, ...] = (".mp4", ".mov", ".webm")

#: What to tell the browser each one is.
MIME_TYPES: dict[str, str] = {".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm"}

#: The name the file has to have for the page to find it.
VIDEO_STEM = "video"

_ID = re.compile(r"^[A-Za-z0-9_-]{4,64}$")
_YOUTUBE_HOSTS = frozenset({"youtube.com", "m.youtube.com", "youtube-nocookie.com"})
_YOUTUBE_PATHS = frozenset({"shorts", "live", "v"})
_VIMEO_HOSTS = frozenset({"vimeo.com", "player.vimeo.com"})
_INSTAGRAM_KINDS = frozenset({"p", "reel"})

#: Named in the message when a link is not one we know how to show.
ACCEPTED_SITES = "YouTube, Vimeo or Instagram"


def find_video_file(folder: Path, *, content_dir: Path, report: Report) -> VideoFile | None:
    """The ``video.mp4`` in a folder, if there is one.

    A video that is in the folder under some other name is not shown, because guessing which of
    several files was meant would be worse than saying so: it earns a note telling her the one
    name that works.
    """
    if not folder.is_dir():
        return None
    candidates = sorted(item for item in folder.iterdir() if item.is_file() and item.suffix.lower() in VIDEO_SUFFIXES)
    chosen = next((item for item in candidates if item.stem.lower() == VIDEO_STEM), None)
    if chosen is None:
        for item in candidates:
            report.notice(
                where=item,
                what=f'This looks like a video, but only a file called "{VIDEO_STEM}{item.suffix.lower()}" '
                f'is shown on the page. Rename it to "{VIDEO_STEM}{item.suffix.lower()}".',
            )
        return None
    relative = chosen.relative_to(content_dir).as_posix()
    return VideoFile(
        source=chosen,
        relative=relative,
        url=f"media/{relative}",
        mime=MIME_TYPES.get(chosen.suffix.lower(), "video/mp4"),
    )


def embed_address(link: str) -> str | None:
    """Turn an ordinary link to a video into one a page can show. ``None`` means "I do not know it"."""
    text = link.strip()
    if not text:
        return None
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"}:
        return None
    host = parsed.netloc.lower().removeprefix("www.")
    parts = [part for part in parsed.path.split("/") if part]
    if host in _YOUTUBE_HOSTS or host == "youtu.be":
        return _from_youtube(text, host=host, parts=parts, query=parsed.query)
    if host in _VIMEO_HOSTS:
        return _from_vimeo(text, host=host, parts=parts)
    if host == "instagram.com":
        return _from_instagram(text, parts=parts)
    return None


def _from_youtube(link: str, *, host: str, parts: list[str], query: str) -> str | None:
    if host == "youtu.be":
        return _youtube(parts[0]) if parts else None
    if not parts:
        return None
    if parts[0] == "embed":
        return link
    if parts[0] == "watch":
        return _youtube(parse_qs(query).get("v", [""])[0])
    if parts[0] in _YOUTUBE_PATHS:
        return _youtube(parts[1]) if parts[1:] else None
    return None


def _from_vimeo(link: str, *, host: str, parts: list[str]) -> str | None:
    if host == "player.vimeo.com":
        return link if parts[:1] == ["video"] else None
    return f"https://player.vimeo.com/video/{parts[0]}" if parts and parts[0].isdigit() else None


def _from_instagram(link: str, *, parts: list[str]) -> str | None:
    if not parts[1:] or parts[0] not in _INSTAGRAM_KINDS:
        return None
    post = parts[1]
    # ``/p/<post>/embed`` is already an embed address. ``/p/embed`` names no post at all, and "embed"
    # is a run of ordinary letters, so without this it would be taken for the post itself.
    if post == "embed":
        return None
    if parts[2:] == ["embed"]:
        return link
    return f"https://www.instagram.com/{parts[0]}/{post}/embed" if _ID.match(post) else None


def _youtube(identifier: str) -> str | None:
    """YouTube without the cookies it would otherwise leave on the visitor's machine."""
    return f"https://www.youtube-nocookie.com/embed/{identifier}" if _ID.match(identifier) else None


def read_video(
    folder: Path, *, link: str, content_dir: Path, path: Path, report: Report
) -> VideoFile | VideoEmbed | None:
    """The video for one collection or runway: the file if there is one, otherwise the link."""
    found = find_video_file(folder, content_dir=content_dir, report=report)
    if found is not None:
        if link:
            report.notice(
                where=path,
                what=f'There is a "video:" line and a {found.source.name} in this folder. '
                "I showed the file. Delete one of the two so it is clear which you meant.",
            )
        return found
    if not link:
        return None
    address = embed_address(link)
    if address is None:
        report.problem(
            where=path,
            what=f'"video: {link}" is not a link I know how to show.',
            fix=f"Open the video on {ACCEPTED_SITES}, copy the address from the bar at the top of the "
            f"browser, and paste that. Or put a {VIDEO_STEM}.mp4 file in this folder instead.",
        )
        return None
    return VideoEmbed(url=address)


def copy_all(videos: list[VideoFile], *, dist_dir: Path, report: Report) -> None:
    """Put every video file into ``dist/`` beside the pictures. Nothing is re-encoded."""
    for video in videos:
        target = dist_dir / video.url
        if _is_up_to_date(target, source=video.source):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copyfile(video.source, target)
        except OSError as error:
            report.problem(
                where=video.source,
                what=f"I could not copy this video onto the website. "
                f"Technical detail: {type(error).__name__}: {error}",
                fix="Check the file opens on your computer, then upload it again.",
            )


def _is_up_to_date(target: Path, *, source: Path) -> bool:
    """Copying a large video on every build is slow, so skip the ones already newer."""
    if not target.is_file():
        return False
    try:
        return target.stat().st_mtime >= source.stat().st_mtime
    except OSError:
        return False
