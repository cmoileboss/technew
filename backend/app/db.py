import os
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, event, func, select
from sqlalchemy.engine import Engine, URL
from sqlalchemy.orm import Session

from .models import Base, Feed

DB_PATH = Path(os.environ.get("TECHNEWS_DB", Path(__file__).resolve().parent.parent / "technews.db"))

DEFAULT_FEEDS = [
    ("CERT-FR - Alertes", "https://www.cert.ssi.gouv.fr/alerte/feed/"),
    ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews"),
    ("Python Insider", "https://blog.python.org/rss.xml"),
    ("Spring Blog", "https://spring.io/blog.atom"),
]

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


class Database:
    def __init__(self) -> None:
        self.engine: Engine | None = None

    @contextmanager
    def connect(self) -> Iterator[Session]:
        engine = self.engine
        if engine is None:
            raise RuntimeError("La base de données n'est pas initialisée.")
        with Session(engine) as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    def init_db(self, seed: bool = True) -> None:
        if self.engine is not None:
            self.engine.dispose()
        engine = _create_engine()
        self.engine = engine
        Base.metadata.create_all(engine)

        with Session(engine) as session:
            if seed and session.scalar(select(func.count()).select_from(Feed)) == 0:
                session.add_all(Feed(title=title, url=url) for title, url in DEFAULT_FEEDS)
                session.commit()


DATABASE = Database()


def connect() -> AbstractContextManager[Session]:
    return DATABASE.connect()


def init_db(seed: bool = True) -> None:
    DATABASE.init_db(seed)
