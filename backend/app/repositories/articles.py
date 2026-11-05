from sqlalchemy import func, select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from ..fetcher import ParsedArticle
from ..models import Article, Feed


class ArticleRepository:
    def __init__(self, session: Session):
        self.session = session

    def unclassified(self, limit: int) -> list[dict]:
        rows = self.session.execute(
            select(Article.id, Article.title, Article.summary)
            .where(Article.theme.is_(None))
            .order_by(Article.id.desc())
            .limit(limit)
        ).mappings()
        return [dict(row) for row in rows]

    def set_themes(self, themes: list[tuple[int, str, float]]) -> None:
        """Store (article id, theme, score) triples."""
        if themes:
            self.session.execute(
                update(Article),
                [{"id": article_id, "theme": theme, "theme_score": score} for article_id, theme, score in themes],
            )

    def add_many(self, feed_id: int, articles: list[ParsedArticle]) -> int:
        """Insert articles ignoring duplicates; return the number of rows actually inserted."""
        if not articles:
            return 0
        statement = insert(Article).values(
            [
                {
                    "feed_id": feed_id,
                    "guid": article.guid,
                    "title": article.title,
                    "link": article.link,
                    "summary": article.summary,
                    "published_at": article.published_at,
                }
                for article in articles
            ]
        )
        result = self.session.execute(
            statement.on_conflict_do_nothing(index_elements=["feed_id", "guid"])
        )
        return max(result.rowcount, 0)

    def published_since(self, since: str) -> list[dict]:
        """Articles published at or after `since` (ISO 8601 UTC), grouped-friendly order."""
        rows = self.session.execute(
            select(
                Feed.title.label("feed_title"),
                Article.title,
                Article.link,
                Article.summary,
                Article.published_at,
            )
            .join(Feed, Article.feed_id == Feed.id)
            .where(Article.published_at >= since)
            .order_by(Feed.title, Article.published_at.desc(), Article.id.desc())
        ).mappings()
        return [dict(row) for row in rows]

    def search(
        self, feed_id: int | None, query: str | None, theme: str | None, limit: int, offset: int
    ) -> tuple[list[dict], int]:
        conditions = []
        if feed_id is not None:
            conditions.append(Article.feed_id == feed_id)
        if theme:
            conditions.append(Article.theme == theme)
        if query and query.strip():
            escaped = query.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped}%"
            conditions.append(
                Article.title.like(pattern, escape="\\")
                | Article.summary.like(pattern, escape="\\")
            )

        total = self.session.scalar(
            select(func.count(Article.id))
            .select_from(Article)
            .where(*conditions)
        )
        rows = self.session.execute(
            select(
                Article.id,
                Article.feed_id,
                Feed.title.label("feed_title"),
                Article.title,
                Article.link,
                Article.summary,
                Article.published_at,
                Article.theme,
                Article.theme_score,
            )
            .join(Feed, Article.feed_id == Feed.id)
            .where(*conditions)
            .order_by(
                Article.published_at.is_(None),
                Article.published_at.desc(),
                Article.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        ).mappings()
        return [dict(row) for row in rows], total or 0
