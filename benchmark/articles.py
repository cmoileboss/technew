import json
import os
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(os.getenv("TECHNEWS_DB", Path(__file__).resolve().parent.parent / "backend" / "technews.db"))
OUTPUT_PATH = Path(__file__).resolve().parent / "articles.json"
PER_FEED = 2


def load_articles(per_feed: int = PER_FEED, db_path: Path = DB_PATH) -> list[dict]:
    """Retourne les `per_feed` articles les plus récents de chaque flux."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        feeds = conn.execute("SELECT id, title FROM feeds ORDER BY id").fetchall()
        articles = []
        for feed in feeds:
            rows = conn.execute(
                "SELECT id, title, link, summary, published_at FROM articles "
                "WHERE feed_id = ? ORDER BY published_at DESC, id DESC LIMIT ?",
                (feed["id"], per_feed),
            ).fetchall()
            articles.extend({"feed": feed["title"], **dict(row)} for row in rows)
    return articles


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    articles = load_articles()
    OUTPUT_PATH.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(articles)} articles écrits dans {OUTPUT_PATH}")
    for article in articles:
        print(f"- [{article['feed']}] {article['title']}")


if __name__ == "__main__":
    main()
