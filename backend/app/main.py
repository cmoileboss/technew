import asyncio
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, HttpUrl

from . import db
from .fetcher import FeedError, ParsedFeed, fetch_feed_content, parse_feed


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="TechNews RSS", lifespan=lifespan)


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


class ArticlePage(BaseModel):
    items: list[ArticleOut]
    total: int


class RefreshResult(BaseModel):
    new_articles: int
    errors: int


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _download(url: str) -> ParsedFeed:
    return parse_feed(await fetch_feed_content(url))


def _store(conn: sqlite3.Connection, feed_id: int, parsed: ParsedFeed) -> int:
    before = conn.total_changes
    conn.executemany(
        "INSERT OR IGNORE INTO articles (feed_id, guid, title, link, summary, published_at) VALUES (?, ?, ?, ?, ?, ?)",
        [(feed_id, a.guid, a.title, a.link, a.summary, a.published_at) for a in parsed.articles],
    )
    conn.execute("UPDATE feeds SET last_fetched_at = ?, last_error = NULL WHERE id = ?", (_now(), feed_id))
    return conn.total_changes - before - 1


FEED_SELECT = """
    SELECT f.*, (SELECT COUNT(*) FROM articles a WHERE a.feed_id = f.id) AS article_count
    FROM feeds f
"""


def _feed_out(conn: sqlite3.Connection, feed_id: int) -> FeedOut:
    row = conn.execute(f"{FEED_SELECT} WHERE f.id = ?", (feed_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Flux introuvable.")
    return FeedOut.model_validate(dict(row))


@app.get("/api/feeds", response_model=list[FeedOut])
def list_feeds():
    with db.connect() as conn:
        rows = conn.execute(f"{FEED_SELECT} ORDER BY f.title COLLATE NOCASE").fetchall()
    return [FeedOut.model_validate(dict(r)) for r in rows]


@app.post("/api/feeds", response_model=FeedOut, status_code=201)
async def add_feed(payload: FeedIn):
    url = str(payload.url)
    with db.connect() as conn:
        if conn.execute("SELECT 1 FROM feeds WHERE url = ?", (url,)).fetchone():
            raise HTTPException(409, "Ce flux existe déjà.")
    try:
        parsed = await _download(url)
    except FeedError as exc:
        raise HTTPException(422, str(exc)) from exc
    title = (payload.title or "").strip() or parsed.title or url
    with db.connect() as conn:
        try:
            feed_id = conn.execute("INSERT INTO feeds (url, title) VALUES (?, ?)", (url, title)).lastrowid
        except sqlite3.IntegrityError as exc:
            raise HTTPException(409, "Ce flux existe déjà.") from exc
        _store(conn, feed_id, parsed)
        return _feed_out(conn, feed_id)


@app.delete("/api/feeds/{feed_id}", status_code=204)
def delete_feed(feed_id: int):
    with db.connect() as conn:
        if conn.execute("DELETE FROM feeds WHERE id = ?", (feed_id,)).rowcount == 0:
            raise HTTPException(404, "Flux introuvable.")
    return Response(status_code=204)


@app.post("/api/refresh", response_model=RefreshResult)
async def refresh_all(feed_id: int | None = None):
    with db.connect() as conn:
        query = "SELECT id, url FROM feeds" + (" WHERE id = ?" if feed_id is not None else "")
        feeds = conn.execute(query, (feed_id,) if feed_id is not None else ()).fetchall()
    if feed_id is not None and not feeds:
        raise HTTPException(404, "Flux introuvable.")

    results = await asyncio.gather(*(_download(f["url"]) for f in feeds), return_exceptions=True)
    new_articles = errors = 0
    with db.connect() as conn:
        for feed, result in zip(feeds, results):
            if isinstance(result, FeedError):
                errors += 1
                conn.execute("UPDATE feeds SET last_error = ? WHERE id = ?", (str(result), feed["id"]))
            elif isinstance(result, BaseException):
                errors += 1
                conn.execute("UPDATE feeds SET last_error = ? WHERE id = ?", ("Erreur inattendue.", feed["id"]))
            else:
                new_articles += _store(conn, feed["id"], result)
    return RefreshResult(new_articles=new_articles, errors=errors)


@app.get("/api/articles", response_model=ArticlePage)
def list_articles(
    feed_id: int | None = None,
    q: str | None = Query(None, max_length=200),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    where, params = [], []
    if feed_id is not None:
        where.append("a.feed_id = ?")
        params.append(feed_id)
    if q and q.strip():
        escaped = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        where.append("(a.title LIKE ? ESCAPE '\\' OR a.summary LIKE ? ESCAPE '\\')")
        params += [f"%{escaped}%"] * 2
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    with db.connect() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM articles a {clause}", params).fetchone()[0]
        rows = conn.execute(
            f"""SELECT a.id, a.feed_id, f.title AS feed_title, a.title, a.link, a.summary, a.published_at
                FROM articles a JOIN feeds f ON f.id = a.feed_id {clause}
                ORDER BY a.published_at IS NULL, a.published_at DESC, a.id DESC
                LIMIT ? OFFSET ?""",
            [*params, limit, offset],
        ).fetchall()
    return ArticlePage(items=[ArticleOut(**dict(r)) for r in rows], total=total)
