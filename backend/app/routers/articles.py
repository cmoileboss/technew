from fastapi import APIRouter, Depends, Query

from ..schemas import ArticlePage
from ..services import ArticleService

router = APIRouter(prefix="/api", tags=["articles"])


def get_article_service() -> ArticleService:
    return ArticleService()


@router.get("/articles", response_model=ArticlePage)
def list_articles(
    feed_id: int | None = None,
    q: str | None = Query(None, max_length=200),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ArticleService = Depends(get_article_service),
):
    return service.list_articles(feed_id, q, limit, offset)
