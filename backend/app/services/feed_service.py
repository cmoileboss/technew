import asyncio

from .. import db
from ..exceptions import ConflictError, NotFoundError, UnprocessableFeedError
from ..fetcher import FeedError, ParsedFeed, fetch_feed_content, parse_feed
from ..repositories import ArticleRepository, FeedRepository
from ..schemas import FeedIn, FeedOut, RefreshResult

FEED_NOT_FOUND = "Flux introuvable."


async def _download(url: str) -> ParsedFeed:
    return parse_feed(await fetch_feed_content(url))


class FeedService:
    def list_feeds(self) -> list[FeedOut]:
        with db.connect() as conn:
            rows = FeedRepository(conn).list_all()
        return [FeedOut.model_validate(dict(r)) for r in rows]

    async def add_feed(self, payload: FeedIn) -> FeedOut:
        url = str(payload.url)
        with db.connect() as conn:
            if FeedRepository(conn).exists_by_url(url):
                raise ConflictError("Ce flux existe déjà.")
        try:
            parsed = await _download(url)
        except FeedError as exc:
            raise UnprocessableFeedError(str(exc)) from exc
        title = (payload.title or "").strip() or parsed.title or url
        with db.connect() as conn:
            feeds = FeedRepository(conn)
            feed_id = feeds.create(url, title)
            ArticleRepository(conn).add_many(feed_id, parsed.articles)
            feeds.mark_fetched(feed_id)
            return FeedOut.model_validate(dict(feeds.get(feed_id)))

    def delete_feed(self, feed_id: int) -> None:
        with db.connect() as conn:
            if not FeedRepository(conn).delete(feed_id):
                raise NotFoundError(FEED_NOT_FOUND)

    async def refresh(self, feed_id: int | None = None) -> RefreshResult:
        with db.connect() as conn:
            targets = FeedRepository(conn).list_targets(feed_id)
        if feed_id is not None and not targets:
            raise NotFoundError(FEED_NOT_FOUND)

        results = await asyncio.gather(*(_download(t["url"]) for t in targets), return_exceptions=True)
        new_articles = errors = 0
        with db.connect() as conn:
            feeds, articles = FeedRepository(conn), ArticleRepository(conn)
            for target, result in zip(targets, results):
                if isinstance(result, FeedError):
                    errors += 1
                    feeds.mark_error(target["id"], str(result))
                elif isinstance(result, BaseException):
                    errors += 1
                    feeds.mark_error(target["id"], "Erreur inattendue.")
                else:
                    new_articles += articles.add_many(target["id"], result.articles)
                    feeds.mark_fetched(target["id"])
        return RefreshResult(new_articles=new_articles, errors=errors)
