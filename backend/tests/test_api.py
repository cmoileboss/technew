from datetime import datetime, timezone

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app import classifier, db, fetcher, main
from app.models import Article, Feed
from app.services import ClassificationService, DigestService, feed_service

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


def test_weekly_digest_groups_recent_articles_by_feed(client):
    client.post("/api/feeds", json={"url": "https://example.com/rss"})
    now = datetime(2025, 11, 5, tzinfo=timezone.utc)

    digest = DigestService().weekly_digest(days=7, now=now)
    assert digest.startswith("# Digest TechNews")
    assert "## Demo (2)" in digest
    assert "- [Second](https://example.com/2) — 2025-11-02" in digest
    assert "> Un résumé" in digest

    short = DigestService().weekly_digest(days=3, now=now)
    assert "## Demo (1)" in short and "Premier" not in short


def test_digest_endpoint_returns_markdown(client):
    r = client.get("/api/digest")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/markdown")
    assert "Aucun article publié sur cette période." in r.text
    assert client.get("/api/digest", params={"days": 0}).status_code == 422
    assert client.get("/api/digest", params={"days": 91}).status_code == 422


class FakeEmbedder: # pylint: disable=too-few-public-methods
    """Embeds a text on the first axis if it mentions 'Premier', otherwise on the second one."""

    def encode(self, texts):
        return np.array([[1.0, 0.0] if "Premier" in text else [0.0, 1.0] for text in texts])


def make_classifier():
    return classifier.ThemeClassifier(
        classes=["sécurité", "framework"],
        coef=np.array([[4.0, -4.0], [-4.0, 4.0]]),
        intercept=np.zeros(2),
        embedder=FakeEmbedder(),
    )


def test_theme_classifier_returns_theme_and_probability():
    results = make_classifier().classify(["Premier article", "Autre chose"])
    assert [theme for theme, _ in results] == ["sécurité", "framework"]
    assert all(0.5 < score <= 1 for _, score in results)
    assert make_classifier().classify([]) == []


def test_shipped_model_is_consistent():
    loaded = classifier.ThemeClassifier.load(embedder=FakeEmbedder())
    assert set(loaded.classes) == {"sécurité", "framework", "ia", "autre"}
    assert loaded.coef.shape == (len(loaded.classes), 384)
    assert loaded.intercept.shape == (len(loaded.classes),)


def test_new_articles_are_classified_and_filterable_by_theme(client, monkeypatch):
    monkeypatch.setattr(classifier, "get_classifier", make_classifier)
    client.post("/api/feeds", json={"url": "https://example.com/rss"})

    items = {a["title"]: a for a in client.get("/api/articles").json()["items"]}
    assert items["Premier"]["theme"] == "sécurité"
    assert items["Second"]["theme"] == "framework"
    assert 0.5 < items["Second"]["theme_score"] <= 1

    page = client.get("/api/articles", params={"theme": "framework"}).json()
    assert [a["title"] for a in page["items"]] == ["Second"]
    assert client.get("/api/articles", params={"theme": "ia"}).json()["total"] == 0


def test_articles_stay_unclassified_without_classifier(client):
    client.post("/api/feeds", json={"url": "https://example.com/rss"})
    items = client.get("/api/articles").json()["items"]
    assert all(a["theme"] is None and a["theme_score"] is None for a in items)


def test_pending_articles_are_classified_once(client, monkeypatch):
    client.post("/api/feeds", json={"url": "https://example.com/rss"})
    monkeypatch.setattr(classifier, "get_classifier", make_classifier)
    assert ClassificationService().classify_pending() == 2
    assert ClassificationService().classify_pending() == 0
    with db.connect() as session:
        assert session.scalar(select(Article.theme).where(Article.title == "Premier")) == "sécurité"


def test_classification_failure_does_not_break_refresh(client, monkeypatch):
    class Broken: # pylint: disable=too-few-public-methods
        def classify(self, _texts):
            raise RuntimeError("boom")

    monkeypatch.setattr(classifier, "get_classifier", Broken)
    assert client.post("/api/feeds", json={"url": "https://example.com/rss"}).status_code == 201
    assert client.get("/api/articles").json()["total"] == 2


def test_init_db_adds_theme_columns_to_existing_database(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "old.db")
    db.init_db(seed=False)
    with db.DATABASE.engine.begin() as connection:
        connection.exec_driver_sql("ALTER TABLE articles DROP COLUMN theme")
        connection.exec_driver_sql("ALTER TABLE articles DROP COLUMN theme_score")
    db.init_db(seed=False)
    with db.connect() as session:
        assert session.scalars(select(Article.theme)).all() == []
