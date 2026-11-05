import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Protocol

import numpy as np

MODEL_PATH = Path(__file__).resolve().parent / "ml" / "theme_model.json"

logger = logging.getLogger(__name__)


class Embedder(Protocol): # pylint: disable=too-few-public-methods
    def encode(self, texts: list[str]) -> np.ndarray:
        """Return one L2-normalised vector per text."""


class SentenceTransformerEmbedder: # pylint: disable=too-few-public-methods
    """Loads the sentence-transformers model on first use (optional, heavy dependency)."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None

    def encode(self, texts: list[str]) -> np.ndarray:
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # pylint: disable=import-outside-toplevel

            self._model = SentenceTransformer(self.model_name)
        return self._model.encode(texts, normalize_embeddings=True)


def article_text(title: str, summary: str) -> str:
    """Same text format as the one used to train the model (see benchmark/classification.py)."""
    return f"{title}. {summary}"


class ThemeClassifier:
    """Multinomial logistic regression on sentence embeddings, exported by benchmark/train_classifier.py."""

    def __init__(self, classes: list[str], coef: np.ndarray, intercept: np.ndarray, embedder: Embedder):
        self.classes = classes
        self.coef = coef
        self.intercept = intercept
        self.embedder = embedder

    @classmethod
    def load(cls, path: Path = MODEL_PATH, embedder: Embedder | None = None) -> "ThemeClassifier":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            classes=data["classes"],
            coef=np.array(data["coef"]),
            intercept=np.array(data["intercept"]),
            embedder=embedder or SentenceTransformerEmbedder(data["embedding_model"]),
        )

    def classify(self, texts: list[str]) -> list[tuple[str, float]]:
        """Return (theme, probability) for each text."""
        if not texts:
            return []
        logits = np.asarray(self.embedder.encode(texts)) @ self.coef.T + self.intercept
        logits -= logits.max(axis=1, keepdims=True)
        probabilities = np.exp(logits)
        probabilities /= probabilities.sum(axis=1, keepdims=True)
        best = probabilities.argmax(axis=1)
        return [(self.classes[i], float(probabilities[row, i])) for row, i in enumerate(best)]


@lru_cache(maxsize=1)
def get_classifier() -> ThemeClassifier | None:
    """Return the shared classifier, or None when the model or its dependencies are unavailable."""
    try:
        theme_classifier = ThemeClassifier.load()
        theme_classifier.embedder.encode(["warm-up"])
    except (OSError, ValueError, KeyError, ImportError) as exc:
        logger.warning("Classification des thèmes désactivée : %s", exc)
        return None
    return theme_classifier
