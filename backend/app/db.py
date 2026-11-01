import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = Path(os.environ.get("TECHNEWS_DB", Path(__file__).resolve().parent.parent / "technews.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS feeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_fetched_at TEXT,
    last_error TEXT
);
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id INTEGER NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
    guid TEXT NOT NULL,
    title TEXT NOT NULL,
    link TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    published_at TEXT,
    UNIQUE (feed_id, guid)
);
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles (published_at DESC);
"""

DEFAULT_FEEDS = [
    ("CERT-FR - Alertes", "https://www.cert.ssi.gouv.fr/alerte/feed/"),
    ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews"),
    ("Python Insider", "https://blog.python.org/rss.xml"),
    ("Spring Blog", "https://spring.io/blog.atom"),
]


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(seed: bool = True) -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        if seed and conn.execute("SELECT COUNT(*) FROM feeds").fetchone()[0] == 0:
            conn.executemany("INSERT INTO feeds (title, url) VALUES (?, ?)", DEFAULT_FEEDS)
