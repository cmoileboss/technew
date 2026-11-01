import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, event, func, select
from sqlalchemy.engine import Engine, URL
from sqlalchemy.orm import Session

from .models import Base, Feed

DB_PATH = Path(os.environ.get("TECHNEWS_DB", Path(__file__).resolve().parent.parent / "technews.db"))

DEFAULT_FEEDS = [
    ("CERT-FR - Alertes", "https://www.cert.ssi.gouv.fr/alerte/feed/"),
    ("The Hacker News", "https://feeds.feedburner.com/TheHackerNews"),
    ("Python Insider", "https://blog.python.org/rss.xml"),
    ("Spring Blog", "https://spring.io/blog.atom"),
]

_engine: Engine | None = None


def _create_engine() -> Engine:
    engine = create_engine(
        URL.create("sqlite", database=str(DB_PATH)),
        connect_args={"check_same_thread": False},
    )
    event.listen(engine, "connect", _enable_foreign_keys)
    return engine


def _enable_foreign_keys(connection, _record) -> None:
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@contextmanager
def connect() -> Iterator[Session]:
    if _engine is None:
        raise RuntimeError("La base de données n'est pas initialisée.")
    with Session(_engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


def init_db(seed: bool = True) -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = _create_engine()
    Base.metadata.create_all(_engine)

    with Session(_engine) as session:
        if seed and session.scalar(select(func.count()).select_from(Feed)) == 0:
            session.add_all(Feed(title=title, url=url) for title, url in DEFAULT_FEEDS)
            session.commit()
