from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from ..fetcher import ParsedArticle
from ..models import Article, Feed


class ArticleRepository:
    def __init__(self, session: Session):
        self.session = session

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

    def search(
        self, feed_id: int | None, query: str | None, limit: int, offset: int
    ) -> tuple[list[dict], int]:
        conditions = []
        if feed_id is not None:
            conditions.append(Article.feed_id == feed_id)
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
