from datetime import datetime, timedelta, timezone
from itertools import groupby

from .. import db
from ..repositories import ArticleRepository


def _escape(text: str) -> str:
    """Escape characters that would break a Markdown link label or heading."""
    for char in ("\\", "[", "]"):
        text = text.replace(char, "\\" + char)
    return text


def render_digest(rows: list[dict], since: datetime, until: datetime) -> str:
    lines = [
        "# Digest TechNews",
        "",
        f"Période : {since:%Y-%m-%d} → {until:%Y-%m-%d} — {len(rows)} article(s).",
    ]
    if not rows:
        lines += ["", "Aucun article publié sur cette période."]
    for feed_title, group in groupby(rows, key=lambda row: row["feed_title"]):
        articles = list(group)
        lines += ["", f"## {_escape(feed_title)} ({len(articles)})", ""]
        for article in articles:
            date = (article["published_at"] or "")[:10]
            lines.append(f"- [{_escape(article['title'])}]({article['link']}) — {date}")
            if article["summary"]:
                lines.append(f"  > {article['summary']}")
    return "\n".join(lines) + "\n"


class DigestService: # pylint: disable=too-few-public-methods
    def weekly_digest(self, days: int = 7, now: datetime | None = None) -> str:
        until = now or datetime.now(timezone.utc)
        since = until - timedelta(days=days)
        with db.connect() as conn:
            rows = ArticleRepository(conn).published_since(since.isoformat())
        return render_digest(rows, since, until)
