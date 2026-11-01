import sqlite3

from ..fetcher import ParsedArticle


class ArticleRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add_many(self, feed_id: int, articles: list[ParsedArticle]) -> int:
        """Insert articles ignoring duplicates; return the number of rows actually inserted."""
        cursor = self.conn.executemany(
            "INSERT OR IGNORE INTO articles (feed_id, guid, title, link, summary, published_at) VALUES (?, ?, ?, ?, ?, ?)",
            [(feed_id, a.guid, a.title, a.link, a.summary, a.published_at) for a in articles],
        )
        return max(cursor.rowcount, 0)

    def search(
        self, feed_id: int | None, query: str | None, limit: int, offset: int
    ) -> tuple[list[sqlite3.Row], int]:
        where: list[str] = []
        params: list[object] = []
        if feed_id is not None:
            where.append("a.feed_id = ?")
            params.append(feed_id)
        if query and query.strip():
            escaped = query.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            where.append("(a.title LIKE ? ESCAPE '\\' OR a.summary LIKE ? ESCAPE '\\')")
            params += [f"%{escaped}%"] * 2
        clause = f"WHERE {' AND '.join(where)}" if where else ""
        total = self.conn.execute(f"SELECT COUNT(*) FROM articles a {clause}", params).fetchone()[0]
        rows = self.conn.execute(
            f"""SELECT a.id, a.feed_id, f.title AS feed_title, a.title, a.link, a.summary, a.published_at
                FROM articles a JOIN feeds f ON f.id = a.feed_id {clause}
                ORDER BY a.published_at IS NULL, a.published_at DESC, a.id DESC
                LIMIT ? OFFSET ?""",
            [*params, limit, offset],
        ).fetchall()
        return rows, total
