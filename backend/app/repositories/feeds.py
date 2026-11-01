import sqlite3
from datetime import datetime, timezone

from ..exceptions import ConflictError

_SELECT = """
    SELECT f.*, (SELECT COUNT(*) FROM articles a WHERE a.feed_id = f.id) AS article_count
    FROM feeds f
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FeedRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def list_all(self) -> list[sqlite3.Row]:
        return self.conn.execute(f"{_SELECT} ORDER BY f.title COLLATE NOCASE").fetchall()

    def get(self, feed_id: int) -> sqlite3.Row | None:
        return self.conn.execute(f"{_SELECT} WHERE f.id = ?", (feed_id,)).fetchone()

    def exists_by_url(self, url: str) -> bool:
        return self.conn.execute("SELECT 1 FROM feeds WHERE url = ?", (url,)).fetchone() is not None

    def list_targets(self, feed_id: int | None = None) -> list[sqlite3.Row]:
        if feed_id is None:
            return self.conn.execute("SELECT id, url FROM feeds").fetchall()
        return self.conn.execute("SELECT id, url FROM feeds WHERE id = ?", (feed_id,)).fetchall()

    def create(self, url: str, title: str) -> int:
        try:
            return self.conn.execute("INSERT INTO feeds (url, title) VALUES (?, ?)", (url, title)).lastrowid
        except sqlite3.IntegrityError as exc:
            raise ConflictError("Ce flux existe déjà.") from exc

    def delete(self, feed_id: int) -> bool:
        return self.conn.execute("DELETE FROM feeds WHERE id = ?", (feed_id,)).rowcount > 0

    def mark_fetched(self, feed_id: int) -> None:
        self.conn.execute(
            "UPDATE feeds SET last_fetched_at = ?, last_error = NULL WHERE id = ?", (_now(), feed_id)
        )

    def mark_error(self, feed_id: int, message: str) -> None:
        self.conn.execute("UPDATE feeds SET last_error = ? WHERE id = ?", (message, feed_id))
