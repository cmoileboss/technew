import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app import db, fetcher, main
from app.models import Feed
from app.services import feed_service

RSS = b"""<?xml version="1.0"?>
<rss version="2.0"><channel><title>Demo</title>
<item><title>Premier</title><link>https://example.com/1</link><guid>g1</guid>
<description>&lt;p&gt;Un &lt;b&gt;r\xc3\xa9sum\xc3\xa9&lt;/b&gt;&lt;/p&gt;</description>
<pubDate>Sat, 01 Nov 2025 10:00:00 GMT</pubDate></item>
<item><title>Second</title><link>https://example.com/2</link><guid>g2</guid>
<pubDate>Sun, 02 Nov 2025 10:00:00 GMT</pubDate></item>
<item><title>Piege</title><link>javascript:alert(1)</link><guid>g3</guid></item>
</channel></rss>"""


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(db, "DEFAULT_FEEDS", [])
    content = {"data": RSS}

    async def fake_fetch(url):
        if content["data"] is None:
            raise fetcher.FeedError("boom")
        return content["data"]

    monkeypatch.setattr(feed_service, "fetch_feed_content", fake_fetch)
    with TestClient(main.app) as c:
        c.content = content
        yield c


def test_parse_feed_cleans_html_and_skips_unsafe_links():
    parsed = fetcher.parse_feed(RSS)
    assert parsed.title == "Demo"
    assert [a.title for a in parsed.articles] == ["Premier", "Second"]
    assert parsed.articles[0].summary == "Un résumé"


def test_invalid_content_rejected():
    with pytest.raises(fetcher.FeedError):
        fetcher.parse_feed(b"not a feed")


def test_init_db_seeds_current_hacker_news_feed(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "seed.db")
    db.init_db()
    with db.connect() as session:
        feed = session.scalar(select(Feed).where(Feed.title == "The Hacker News"))
        assert feed is not None
        assert feed.url == "https://feeds.feedburner.com/TheHackersNews"


def test_add_feed_list_and_dedupe(client):
    r = client.post("/api/feeds", json={"url": "https://example.com/rss"})
    assert r.status_code == 201
    assert r.json()["title"] == "Demo" and r.json()["article_count"] == 2
    assert client.post("/api/feeds", json={"url": "https://example.com/rss"}).status_code == 409

    page = client.get("/api/articles").json()
    assert page["total"] == 2
    assert [a["title"] for a in page["items"]] == ["Second", "Premier"]

    assert client.get("/api/articles", params={"q": "résumé"}).json()["total"] == 1
    assert client.get("/api/articles", params={"q": "%"}).json()["total"] == 0


def test_refresh_only_adds_new_and_reports_errors(client):
    client.post("/api/feeds", json={"url": "https://example.com/rss"})
    assert client.post("/api/refresh").json() == {"new_articles": 0, "errors": 0}

    client.content["data"] = None
    result = client.post("/api/refresh").json()
    assert result["errors"] == 1
    assert client.get("/api/feeds").json()[0]["last_error"] == "boom"


def test_add_feed_failure_and_delete(client):
    client.content["data"] = None
    assert client.post("/api/feeds", json={"url": "https://bad.example/rss"}).status_code == 422
    client.content["data"] = RSS
    feed_id = client.post("/api/feeds", json={"url": "https://example.com/rss"}).json()["id"]
    assert client.delete(f"/api/feeds/{feed_id}").status_code == 204
    assert client.get("/api/articles", params={"feed_id": feed_id}).json()["total"] == 0
    assert client.delete(f"/api/feeds/{feed_id}").status_code == 404


@pytest.mark.asyncio
async def test_ssrf_guard_blocks_private_and_bad_scheme():
    for url in ("http://127.0.0.1/rss", "file:///etc/passwd", "http://169.254.169.254/"):
        with pytest.raises(fetcher.FeedError):
            await fetcher.fetch_feed_content(url)
