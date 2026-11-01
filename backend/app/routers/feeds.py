from fastapi import APIRouter, Depends, Response

from ..schemas import FeedIn, FeedOut, RefreshResult
from ..services import FeedService

router = APIRouter(prefix="/api", tags=["feeds"])


def get_feed_service() -> FeedService:
    return FeedService()


@router.get("/feeds", response_model=list[FeedOut])
def list_feeds(service: FeedService = Depends(get_feed_service)):
    return service.list_feeds()


@router.post("/feeds", response_model=FeedOut, status_code=201)
async def add_feed(payload: FeedIn, service: FeedService = Depends(get_feed_service)):
    return await service.add_feed(payload)


@router.delete("/feeds/{feed_id}", status_code=204)
def delete_feed(feed_id: int, service: FeedService = Depends(get_feed_service)):
    service.delete_feed(feed_id)
    return Response(status_code=204)


@router.post("/refresh", response_model=RefreshResult)
async def refresh(feed_id: int | None = None, service: FeedService = Depends(get_feed_service)):
    return await service.refresh(feed_id)
