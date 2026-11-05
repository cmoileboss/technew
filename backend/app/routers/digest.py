from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from ..services import DigestService

router = APIRouter(prefix="/api", tags=["digest"])


def get_digest_service() -> DigestService:
    return DigestService()


@router.get("/digest", response_class=PlainTextResponse)
def get_digest(
    days: int = Query(7, ge=1, le=90),
    service: DigestService = Depends(get_digest_service),
):
    return PlainTextResponse(
        service.weekly_digest(days), media_type="text/markdown; charset=utf-8"
    )
