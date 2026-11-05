from pydantic import BaseModel, HttpUrl


class FeedIn(BaseModel):
    url: HttpUrl
    title: str | None = None


class FeedOut(BaseModel):
    id: int
    url: str
    title: str
    last_fetched_at: str | None
    last_error: str | None
    article_count: int


class ArticleOut(BaseModel):
    id: int
    feed_id: int
    feed_title: str
    title: str
    link: str
    summary: str
    published_at: str | None
    theme: str | None = None
    theme_score: float | None = None


class ArticlePage(BaseModel):
    items: list[ArticleOut]
    total: int


class RefreshResult(BaseModel):
    new_articles: int
    errors: int
