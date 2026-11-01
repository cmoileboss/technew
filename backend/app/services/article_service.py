from .. import db
from ..repositories import ArticleRepository
from ..schemas import ArticleOut, ArticlePage


class ArticleService:
    def list_articles(self, feed_id: int | None, query: str | None, limit: int, offset: int) -> ArticlePage:
        with db.connect() as conn:
            rows, total = ArticleRepository(conn).search(feed_id, query, limit, offset)
        return ArticlePage(items=[ArticleOut(**dict(r)) for r in rows], total=total)
