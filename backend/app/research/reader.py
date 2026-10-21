"""Fetch a public page and reduce it to text. Scripts are never executed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin

import httpx

from app.research.errors import ReaderError, TransientFailure, UnsafeURL, retry
from app.research.safety import Resolver, SystemResolver, assert_resolves_public, screen_url

REDIRECTS = {301, 302, 303, 307, 308}
USER_AGENT = "FieldGuideResearch/0.2"
ALLOWED_TYPES = ("text/html", "text/plain", "application/xhtml+xml", "application/json")


@dataclass(frozen=True)
class FetchedPage:
    url: str
    title: str
    text: str
    retrieved_at: datetime


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip = 0
        self._parts: list[str] = []
        self._title: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript", "template", "iframe", "object", "embed"}:
            self._skip += 1
        if tag == "title" and self._skip == 0:
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "template", "iframe", "object", "embed"} and self._skip:
            self._skip -= 1
        if tag == "title":
            self._in_title = False
        if tag in {"p", "div", "li", "br", "h1", "h2", "h3", "tr", "section"}:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        if self._in_title:
            self._title.append(data)
        else:
            self._parts.append(data)

    @property
    def title(self) -> str:
        return " ".join("".join(self._title).split())

    @property
    def text(self) -> str:
        return "\n".join(line.strip() for line in "".join(self._parts).splitlines() if line.strip())


def _decode(body: bytes, content_type: str) -> str:
    charset = "utf-8"
    lowered = content_type.lower()
    if "charset=" in lowered:
        charset = lowered.split("charset=", 1)[1].split(";", 1)[0].strip(" \"'")
    if charset.lower() not in {"utf-8", "utf8", "us-ascii", "ascii", "iso-8859-1", "latin-1"}:
        charset = "utf-8"
    return body.decode(charset, errors="replace")


def extract_text(body: bytes, content_type: str, max_chars: int) -> tuple[str, str]:
    if "\x00" in body.decode("latin-1"):
        raise ReaderError("The page is not a text document.", "unsupported_type")
    media = content_type.split(";", 1)[0].strip().lower()
    if media and not any(media.startswith(allowed) for allowed in ALLOWED_TYPES):
        if not body.lstrip().startswith(b"<"):
            raise ReaderError("The page is not a text document.", "unsupported_type")
    decoded = _decode(body, content_type)
    if media.startswith("text/html") or media.startswith("application/xhtml") or decoded.lstrip().startswith("<"):
        parser = _TextExtractor()
        parser.feed(decoded)
        title = parser.title or "Untitled page"
        text = parser.text
    else:
        lines = [line.strip() for line in decoded.splitlines() if line.strip()]
        title = lines[0][:200] if lines else "Untitled page"
        text = "\n".join(lines)
    text = "".join(char for char in text if char in "\n\t" or ord(char) >= 32)
    if not text.strip():
        raise ReaderError("The page had no readable text.", "empty_page")
    return title[:200], text[:max_chars]


class PageReader:
    def __init__(
        self,
        *,
        resolver: Resolver | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 10,
        max_bytes: int = 500_000,
        max_chars: int = 8_000,
        max_redirects: int = 3,
    ) -> None:
        self._resolver = resolver or SystemResolver()
        self._transport = transport
        self._timeout = timeout
        self._max_bytes = max_bytes
        self._max_chars = max_chars
        self._max_redirects = max_redirects

    def read(self, url: str) -> FetchedPage:
        current = screen_url(url)
        assert_resolves_public(current, self._resolver)

        def once() -> FetchedPage:
            try:
                return self._fetch(current)
            except httpx.TimeoutException as exc:
                raise TransientFailure("The page request timed out.", "page_timeout") from exc
            except httpx.InvalidURL as exc:
                raise UnsafeURL("That address is not a public website.", code="blocked_address") from exc
            except httpx.TransportError as exc:
                raise TransientFailure("The page could not be reached.", "page_unavailable") from exc

        return retry(once)

    def _fetch(self, url: str) -> FetchedPage:
        headers = {"User-Agent": USER_AGENT, "Accept": "text/html,text/plain,application/xhtml+xml"}
        with httpx.Client(
            timeout=self._timeout,
            transport=self._transport,
            trust_env=False,
            follow_redirects=False,
        ) as client:
            current = url
            for _hop in range(self._max_redirects + 1):
                assert_resolves_public(current, self._resolver)
                with client.stream("GET", current, headers=headers) as response:
                    if response.status_code in REDIRECTS:
                        location = response.headers.get("location")
                        if not location:
                            raise ReaderError("The page redirect had no destination.", "bad_redirect")
                        try:
                            current = screen_url(urljoin(str(response.url), location))
                        except UnsafeURL as exc:
                            raise UnsafeURL(
                                "The page redirected to a non-public address.",
                                code="unsafe_redirect",
                            ) from exc
                        continue
                    if response.status_code in {429, 500, 502, 503, 504}:
                        raise TransientFailure("The page did not load.", "page_unavailable")
                    if response.status_code != 200:
                        raise ReaderError("The page did not load.", "page_unavailable")
                    content_type = response.headers.get("content-type", "")
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        if len(body) + len(chunk) > self._max_bytes:
                            raise ReaderError("The page is too large to read.", "page_too_large")
                        body.extend(chunk)
                    title, text = extract_text(bytes(body), content_type, self._max_chars)
                    return FetchedPage(
                        url=current,
                        title=title,
                        text=text,
                        retrieved_at=datetime.now(timezone.utc),
                    )
        raise ReaderError("The page redirected too many times.", "too_many_redirects")
