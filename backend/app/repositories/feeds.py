from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..exceptions import ConflictError
from ..models import Article, Feed


class FeedRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> list[dict]:
        article_count = (
            select(func.count(Article.id))
            .where(Article.feed_id == Feed.id)
            .correlate(Feed)
            .scalar_subquery()
        )
        rows = self.session.execute(
            select(
                Feed.id,
                Feed.url,
                Feed.title,
                Feed.last_fetched_at,
                Feed.last_error,
                article_count.label("article_count"),
            ).order_by(Feed.title.collate("NOCASE"))
        )
        return [dict(row) for row in rows.mappings()]

    def get(self, feed_id: int) -> dict | None:
        article_count = (
            select(func.count(Article.id))
            .where(Article.feed_id == Feed.id)
            .correlate(Feed)
            .scalar_subquery()
        )
        row = self.session.execute(
            select(
                Feed.id,
                Feed.url,
                Feed.title,
                Feed.last_fetched_at,
                Feed.last_error,
                article_count.label("article_count"),
            ).where(Feed.id == feed_id)
        ).mappings().one_or_none()
        return dict(row) if row is not None else None

    def exists_by_url(self, url: str) -> bool:
        return self.session.scalar(select(Feed.id).where(Feed.url == url)) is not None

    def list_targets(self, feed_id: int | None = None) -> list[dict]:
        query = select(Feed.id, Feed.url)
        if feed_id is not None:
            query = query.where(Feed.id == feed_id)
        return [dict(row) for row in self.session.execute(query).mappings()]

    def create(self, url: str, title: str) -> int:
        feed = Feed(url=url, title=title)
        self.session.add(feed)
        try:
            self.session.flush()
        except IntegrityError as exc:
            raise ConflictError("Ce flux existe déjà.") from exc
        return feed.id

    def delete(self, feed_id: int) -> bool:
        result = self.session.execute(delete(Feed).where(Feed.id == feed_id))
        return result.rowcount > 0

    def mark_fetched(self, feed_id: int) -> None:
        self.session.execute(
            update(Feed)
            .where(Feed.id == feed_id)
            .values(last_fetched_at=datetime.now(timezone.utc).isoformat(), last_error=None)
        )

    def mark_error(self, feed_id: int, message: str) -> None:
        self.session.execute(
            update(Feed).where(Feed.id == feed_id).values(last_error=message)
        )
