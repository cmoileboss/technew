import asyncio
import calendar
import html
import ipaddress
import re
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import feedparser
import httpx

MAX_BYTES = 5 * 1024 * 1024
MAX_REDIRECTS = 5
TIMEOUT = 15.0
SUMMARY_MAX = 500
USER_AGENT = "TechNewsAI/0.1 (+RSS reader)"

_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")


class FeedError(Exception):
    """Raised when a feed cannot be fetched or parsed."""


@dataclass
class ParsedArticle:
    guid: str
    title: str
    link: str
    summary: str
    published_at: str | None


@dataclass
class ParsedFeed:
    title: str
    articles: list[ParsedArticle]


async def _assert_public_url(url: str) -> None:
    """Reject non-http(s) URLs and hosts resolving to private/internal addresses (SSRF guard)."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise FeedError("URL invalide : seuls http et https sont acceptés.")
    try:
        infos = await asyncio.to_thread(socket.getaddrinfo, parsed.hostname, parsed.port)
    except socket.gaierror as exc:
        raise FeedError(f"Hôte introuvable : {parsed.hostname}") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise FeedError("L'adresse du flux pointe vers un réseau privé ou interne.")


async def fetch_feed_content(url: str) -> bytes:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    }
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=False, headers=headers) as client:
        current = url
        for _ in range(MAX_REDIRECTS + 1):
            await _assert_public_url(current)
            try:
                async with client.stream("GET", current) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise FeedError("Redirection sans destination.")
                        current = urljoin(current, location)
                        continue
                    if response.status_code >= 400:
                        raise FeedError(f"Le serveur a répondu {response.status_code}.")
                    data = bytearray()
                    async for chunk in response.aiter_bytes():
                        data.extend(chunk)
                        if len(data) > MAX_BYTES:
                            raise FeedError("Flux trop volumineux.")
                    return bytes(data)
            except httpx.HTTPError as exc:
                raise FeedError(f"Erreur réseau : {exc.__class__.__name__}") from exc
        raise FeedError("Trop de redirections.")


def _clean(text: str) -> str:
    return _SPACE_RE.sub(" ", html.unescape(_TAG_RE.sub(" ", text))).strip()


def _entry_date(entry) -> str | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc).isoformat()


def parse_feed(content: bytes) -> ParsedFeed:
    feed = feedparser.parse(content)
    if feed.bozo and not feed.entries:
        raise FeedError("Le contenu n'est pas un flux RSS/Atom valide.")
    articles = []
    for entry in feed.entries:
        link = entry.get("link", "")
        if urlparse(link).scheme not in ("http", "https"):
            continue
        title = _clean(entry.get("title", "")) or link
        summary = _clean(entry.get("summary", "") or "")
        if len(summary) > SUMMARY_MAX:
            summary = summary[: SUMMARY_MAX - 1].rstrip() + "…"
        articles.append(
            ParsedArticle(
                guid=entry.get("id") or link,
                title=title,
                link=link,
                summary=summary,
                published_at=_entry_date(entry),
            )
        )
    return ParsedFeed(title=_clean(feed.feed.get("title", "")), articles=articles)
