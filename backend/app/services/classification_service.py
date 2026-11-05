import logging

from .. import classifier, db
from ..repositories import ArticleRepository

BATCH_SIZE = 500

logger = logging.getLogger(__name__)


class ClassificationService: # pylint: disable=too-few-public-methods
    def classify_pending(self, limit: int = BATCH_SIZE) -> int:
        """Assign a theme to articles that have none; never raises (articles simply stay unclassified)."""
        theme_classifier = classifier.get_classifier()
        if theme_classifier is None:
            return 0
        try:
            with db.connect() as conn:
                articles = ArticleRepository(conn)
                pending = articles.unclassified(limit)
                results = theme_classifier.classify(
                    [classifier.article_text(row["title"], row["summary"]) for row in pending]
                )
                articles.set_themes(
                    [(row["id"], theme, score) for row, (theme, score) in zip(pending, results)]
                )
            return len(pending)
        except Exception: # pylint: disable=broad-exception-caught
            logger.exception("Échec de la classification des articles")
            return 0
