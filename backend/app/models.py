from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Feed(Base):
    __tablename__ = "feeds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(
        String, nullable=False, server_default=func.current_timestamp()
    )
    last_fetched_at: Mapped[str | None] = mapped_column(String)
    last_error: Mapped[str | None] = mapped_column(String)
    articles: Mapped[list["Article"]] = relationship(
        back_populates="feed", cascade="all, delete-orphan", passive_deletes=True
    )


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint("feed_id", "guid"),
        Index("idx_articles_published", text("published_at DESC")),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feed_id: Mapped[int] = mapped_column(
        ForeignKey("feeds.id", ondelete="CASCADE"), nullable=False
    )
    guid: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    link: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    published_at: Mapped[str | None] = mapped_column(String)
    feed: Mapped[Feed] = relationship(back_populates="articles")
